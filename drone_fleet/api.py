"""REST API exposing fleet controls to logistics platforms."""
from typing import Dict, Tuple, List
import logging
import time
import secrets
from pathlib import Path
try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter
except Exception:  # pragma: no cover - optional dependency
    CONTENT_TYPE_LATEST = "text/plain"
    def generate_latest():
        return b""
    class Counter:  # type: ignore
        def __init__(self, *a, **k):
            pass
        def labels(self, **_):
            class C:
                def inc(self, *_args, **_kwargs):
                    pass
            return C()

try:
    from fastapi import FastAPI, Request, Response, Depends
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore
    Request = Response = None  # type: ignore


class FleetAPI:
    """Wrapper around FastAPI to expose endpoints."""

    def __init__(self, api_keys: Dict[str, Tuple[str, float | None]] | None = None, rate_limit: int = 100):
        if FastAPI is None:
            raise ImportError("FastAPI is required to run the API")
        self.app = FastAPI()
        self.api_keys = api_keys or {"secret": ("tenant_default", None)}
        self.rate_limit = rate_limit
        self.token_bucket: Dict[str, tuple[float, int]] = {}
        self.revoked_keys: set[str] = set()
        self.logger = logging.getLogger(__name__)
        self.request_counter = Counter(
            "api_requests_total",
            "API requests",
            ["endpoint", "tenant", "user", "error_code"],
            registry=None,
        )
        self.request_logs: Dict[str, Dict[str, List[str]]] = {}
        Path("logs").mkdir(exist_ok=True)
        self.audit_log = Path("logs/security.log")
        try:
            from prometheus_client import Gauge
            import psutil
            self.cpu_gauge = Gauge("system_cpu_percent", "CPU usage")
            self.mem_gauge = Gauge("system_mem_bytes", "Memory usage")
            self._collect_system_metrics = lambda: (
                self.cpu_gauge.set(psutil.cpu_percent()),
                self.mem_gauge.set(psutil.virtual_memory().used),
            )
        except Exception:  # pragma: no cover - optional deps
            self._collect_system_metrics = lambda: None
        from .auth import router as auth_router, require_role, create_user, key_counter
        from .portal import router as portal_router, init as portal_init
        create_user("operator", "operator", role="operator")
        self.require_admin = require_role("admin")
        self.app.include_router(auth_router)
        portal_init(self)
        self.app.include_router(portal_router)
        self._setup_routes()

    def revoke_key(self, key: str) -> None:
        """Revoke an API key so it can no longer be used."""
        self.revoked_keys.add(key)
        self._log_security(f"revoked:{key}")

    def add_key(self, key: str, tenant: str, ttl: float | None = None) -> None:
        """Register a new API key with optional expiry time."""
        expiry = time.time() + ttl if ttl else None
        self.api_keys[key] = (tenant, expiry)
        self._log_security(f"added:{key}:{tenant}:{expiry}")

    def rotate_key(self, old_key: str) -> str:
        """Generate a new key and revoke the old one."""
        info = self.api_keys.get(old_key)
        if info is None:
            raise KeyError(old_key)
        new_key = secrets.token_urlsafe(16)
        self.add_key(new_key, info[0], ttl=None if info[1] is None else info[1] - time.time())
        self.revoke_key(old_key)
        self._log_security(f"rotated:{old_key}->{new_key}")
        return new_key

    def _log_security(self, event: str, tenant: str | None = None) -> None:
        log_path = self.audit_log
        if tenant:
            log_path = Path("logs") / tenant / "security.log"
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"{time.time()}:{event}\n")
        except Exception:
            pass

    def _allow_request(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self.token_bucket.get(key)
        if bucket is None:
            self.token_bucket[key] = (now, self.rate_limit - 1)
            return True
        last, tokens = bucket
        tokens = min(self.rate_limit, tokens + int(now - last))
        if tokens <= 0:
            self.token_bucket[key] = (now, tokens)
            return False
        self.token_bucket[key] = (now, tokens - 1)
        return True

    def _setup_routes(self) -> None:
        @self.app.middleware("http")
        async def metrics_middleware(request: Request, call_next):
            key = request.headers.get("X-API-Key", "")
            user = request.headers.get("X-User", "anon")
            info = self.api_keys.get(key)
            if key in self.revoked_keys or (info and info[1] and info[1] < time.time()):
                self.logger.warning("Attempt with revoked/expired key: %s", key)
                self._log_security(f"denied:{key}", tenant=info[0] if info else None)
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail="invalid api key")
            if info is None:
                self.logger.warning("Unknown API key used")
                self._log_security(f"unknown_key:{key}")
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail="invalid api key")
            tenant = info[0]
            if not self._allow_request(key):
                self._log_security(f"rate_limited:{key}", tenant=tenant)
                from fastapi import HTTPException
                raise HTTPException(status_code=429, detail="rate limit", headers={"Retry-After": "1"})
            start = time.time()
            key_counter.inc()
            response = await call_next(request)
            if self.request_counter:
                self.request_counter.labels(endpoint=request.url.path, tenant=tenant, user=user, error_code=response.status_code).inc()
            self._collect_system_metrics()
            self.request_logs.setdefault(tenant, {}).setdefault(user, []).append(f"{start}:{request.url.path}:{response.status_code}")
            return response

        @self.app.get("/status")
        def status() -> Dict[str, str]:
            return {"status": "ok"}

        @self.app.get("/health")
        def health() -> Dict[str, str]:
            return {"health": "ok"}

        @self.app.get("/readiness")
        def readiness() -> Dict[str, str]:
            return {"ready": True}

        @self.app.post("/blockchain/tx")
        def new_tx() -> Dict[str, str]:
            return {"tx": "accepted"}

        @self.app.post("/blockchain/trade")
        def trade(data: Dict[str, str]) -> Dict[str, str]:
            return {"trade": "recorded", **data}

        @self.app.post("/delivery")
        def new_delivery(order: Dict[str, str]) -> Dict[str, str]:
            return {"order": "accepted", **order}

        @self.app.get("/metrics")
        def metrics() -> Response:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

        @self.app.get("/data_export/{tenant}/{user}")
        def data_export(tenant: str, user: str) -> Dict[str, List[str]]:
            return {"logs": self.request_logs.get(tenant, {}).get(user, [])}

        @self.app.delete("/user/{tenant}/{user}")
        def delete_user(tenant: str, user: str) -> Dict[str, str]:
            self.request_logs.get(tenant, {}).pop(user, None)
            self._log_security(f"delete_user:{tenant}:{user}", tenant=tenant)
            return {"deleted": user}

        @self.app.post("/admin/rotate_key")
        def rotate_key_endpoint(old_key: str, user: str = Depends(self.require_admin)) -> Dict[str, str]:
            new_key = self.rotate_key(old_key)
            tenant = self.api_keys.get(new_key, ("", None))[0]
            self._log_security(f"rotated_via_endpoint:{old_key}->{new_key}", tenant=tenant)
            return {"new_key": new_key}
