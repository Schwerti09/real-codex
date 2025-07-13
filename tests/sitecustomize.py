import sys, types, os

def _ensure(name: str, attrs: dict | None = None):
    if name in sys.modules:
        return
    module = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(module, k, v)
    sys.modules[name] = module

_ensure(
    'fastapi',
    {
        'FastAPI': type('FastAPI', (), {}),
        'Depends': lambda f=None: None,
        'HTTPException': type('HTTPException', (Exception,), {}),
    },
)
_ensure('fastapi.responses', {'JSONResponse': lambda *a, **k: None})
_ensure('fastapi.security', {'OAuth2PasswordBearer': lambda *a, **k: None})

_ensure('prometheus_client', {'Counter': lambda *a, **k: type('C',(),{"inc":lambda self: None,"labels":lambda self,*a,**k:self})()})


if 'torch' not in sys.modules:
    mod = types.ModuleType('torch')
    mod.__fake__ = True
    class cuda:
        @staticmethod
        def is_available() -> bool:
            return False
    mod.cuda = cuda
    sys.modules['torch'] = mod

# ensure project root is on path for imports
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
