from chatbot.infrastructure.chat_service import ChatService

class DummyPlugin(ChatService):
    name = "dummy"

    def chat(self, prompt: str) -> str:
        return "dummy:" + prompt

def get_chat_service() -> ChatService:
    return DummyPlugin()
