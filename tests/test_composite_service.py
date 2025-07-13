import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chatbot import CompositeChatService, load_plugins

class FailService:
    name = "fail"
    def send_message(self, prompt: str) -> str:
        raise RuntimeError("failed")

class SuccessService:
    name = "ok"
    def __init__(self):
        self.called = False
    def send_message(self, prompt: str) -> str:
        self.called = True
        return f"ok:{prompt}"

def test_fallback():
    service = CompositeChatService([FailService(), SuccessService()])
    resp = service.send_message("hi")
    assert resp == "ok:hi"


def test_plugin_loading(tmp_path):
    plugin_file = tmp_path / "plug.py"
    plugin_file.write_text(
        """
class MyService:
    name = 'plugin'
    def send_message(self, prompt):
        return f'plugin:{prompt}'

def get_service():
    return MyService()
"""
    )
    os.environ['CHATBOT_PLUGIN_PATHS'] = str(plugin_file)
    plugins = load_plugins()
    assert plugins and plugins[0].send_message('x') == 'plugin:x'
    # CompositeChatService should include plugin by default
    comp = CompositeChatService()
    found = any(s.name == 'plugin' for s in comp.services)
    assert found
