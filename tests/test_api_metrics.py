import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from drone_fleet.api import FleetAPI, FastAPI


def test_metrics_endpoint():
    if FastAPI is None:
        return
    api = FleetAPI(rate_limit=1)
    from fastapi.testclient import TestClient
    client = TestClient(api.app)
    headers = {"X-API-Key": "secret", "X-User": "u1"}
    resp = client.get("/status", headers=headers)
    assert resp.status_code == 200
    resp = client.get("/metrics", headers=headers)
    assert resp.status_code == 200
    assert b"api_requests_total" in resp.content

    # rate limiting
    resp2 = client.get("/status", headers=headers)
    assert resp2.status_code == 429
    assert resp2.headers.get("Retry-After") == "1"

    # health endpoints
    assert client.get("/health", headers=headers).status_code == 200
    assert client.get("/readiness", headers=headers).status_code == 200

    # invalid key
    bad = client.get("/status", headers={"X-API-Key": "bad"})
    assert bad.status_code == 403

    # expired key
    api.add_key("tmp", "t1", ttl=-1)
    exp = client.get("/status", headers={"X-API-Key": "tmp"})
    assert exp.status_code == 403

    # rotate key
    new_key = api.rotate_key("secret")
    ok = client.get("/status", headers={"X-API-Key": new_key})
    assert ok.status_code == 200
    old = client.get("/status", headers=headers)
    assert old.status_code == 403

    # data export and delete
    export = client.get(f"/data_export/tenant_default/u1", headers={"X-API-Key": new_key, "X-User": "u1"})
    assert export.status_code == 200
    assert export.json()["logs"]
    delete = client.delete(f"/user/tenant_default/u1", headers={"X-API-Key": new_key})
    assert delete.status_code == 200
