import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import numpy  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    numpy = types.ModuleType("numpy")
    import math, random

    def exp(x):
        return math.exp(x)

    class Random:
        uniform = staticmethod(random.uniform)

    def array(obj, dtype=None):
        return obj

    def zeros(shape, dtype=float):
        if isinstance(shape, int):
            return [0.0] * shape
        return [[0.0 for _ in range(shape[1])] for _ in range(shape[0])]

    def mean(seq):
        return sum(seq) / len(seq)

    def std(seq):
        m = mean(seq)
        return (sum((x - m) ** 2 for x in seq) / len(seq)) ** 0.5

    numpy.exp = exp
    numpy.random = Random()
    numpy.array = array
    numpy.zeros = zeros
    numpy.mean = mean
    numpy.std = std
    numpy.float32 = float
    numpy.sum = sum
    sys.modules['numpy'] = numpy

def _ensure(name: str, attrs: dict | None = None) -> None:
    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod

_ensure(
    'fastapi',
    {
        'FastAPI': type('FastAPI', (), {
            '__init__': lambda self, *a, **k: None,
            'include_router': lambda *a, **k: None,
            'post': lambda *a, **k: (lambda f: f),
            'get': lambda *a, **k: (lambda f: f)
        }),
        'APIRouter': type('APIRouter', (), {'post': lambda *a, **k: (lambda f: f), 'get': lambda *a, **k: (lambda f: f)}),
        'Depends': lambda f=None: None,
        'HTTPException': type('HTTPException', (Exception,), {}),
    },
)
_ensure('fastapi.responses', {'JSONResponse': lambda *a, **k: None})
_ensure('fastapi.security', {
    'OAuth2PasswordBearer': lambda *a, **k: None,
    'OAuth2PasswordRequestForm': type('F', (), {})
})
_ensure('prometheus_client', {'Counter': lambda *a, **k: type('C',(),{"inc":lambda self: None,"labels":lambda self,*a,**k:self})()})
_ensure('cryptography', {})
_ensure('cryptography.fernet', {'Fernet': type('Fernet', (), {'generate_key': staticmethod(lambda: b"x"), '__init__': lambda self, key: None})})
_ensure('passlib.context', {'CryptContext': lambda *a, **k: type('CC', (), {'hash': lambda self, pwd: pwd, 'verify': lambda self, pwd, hashed: True})()})
_ensure('httpx', {})

import torch

if not torch.cuda.is_available():
    os.environ["ACCELERATE_DISABLE_RICH"] = "1"
