"""Mistral Cloud API provider for V.E.R.A."""

from typing import Generator
from .llm_provider import LLMProvider


class MistralAPIProvider(LLMProvider):
    """LLM provider using the official Mistral AI Cloud API."""

    def __init__(self, api_key: str, model: str = "mistral-large-latest",
                 temperature: float = 0.7, max_tokens: int = 4096):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from mistralai.client import Mistral
                self._client = Mistral(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Mistral AI SDK not installed. Run: pip install mistralai"
                )
        return self._client

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        response = client.chat.complete(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        return response.choices[0].message.content

    def chat_stream(self, messages: list[dict[str, str]], **kwargs) -> Generator[str, None, None]:
        client = self._get_client()
        stream = client.chat.stream(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        for chunk in stream:
            if chunk.data.choices and chunk.data.choices[0].delta.content:
                yield chunk.data.choices[0].delta.content

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            client.models.list()
            return True
        except Exception:
            return False

    def get_model_name(self) -> str:
        return self.model
