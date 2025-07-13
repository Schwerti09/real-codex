from llm_manager import LLMManager


class DummyModel:
    def respond(self, prompt, ctx):
        return "dummy"


def test_fallback():
    mgr = LLMManager()
    # register two dummy models
    import types

    module = types.ModuleType("mod")
    module.Model = DummyModel
    import sys
    sys.modules["mod"] = module
    mgr.register("m1", "mod")
    mgr.register("m2", "mod")
    mgr.update_accuracy("m1", 0.9)
    mgr.update_accuracy("m2", 0.5)
    assert mgr.get_model() is not None
    mgr.update_accuracy("m1", 0.8)
    model = mgr.get_model()
    assert model is not None


def test_metrics_increment():
    try:
        from prometheus_client import REGISTRY
    except Exception:
        return
    mgr = LLMManager()
    import types, sys
    module = types.ModuleType("mod2")
    class DM:
        def respond(self, prompt, ctx):
            return "ok"
    module.Model = DM
    sys.modules["mod2"] = module
    mgr.register("demo", "mod2")
    mgr.send_prompt("demo", "hello world")
    value = REGISTRY.get_sample_value(
        "llm_requests_total", labels={"model": "demo", "user_id": "anon", "tenant": "default"}
    )
    assert value == 1.0
