import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chatbot import CompositeChatService
from chatbot.services import GrokService, OpenAIService

class TestService(GrokService):
    def send_message(self, prompt: str) -> str:
        if prompt == 'fail':
            raise RuntimeError('boom')
        return 'grok:' + prompt

def test_provider_order():
    svc = CompositeChatService([TestService(), OpenAIService()])
    assert svc.send_message('hi') == 'grok:hi'
    assert svc.send_message('fail').startswith('openai:')
