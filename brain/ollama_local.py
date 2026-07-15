"""Ollama local LLM provider for V.E.R.A."""

from typing import Generator
from .llm_provider import LLMProvider


class OllamaProvider(LLMProvider):
    """LLM provider using a local Ollama instance."""

    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434",
                 temperature: float = 0.7):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.base_url)
            except ImportError:
                raise ImportError(
                    "Ollama Python package not installed. Run: pip install ollama"
                )
        return self._client

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        response = client.chat(
            model=kwargs.get("model", self.model),
            messages=messages,
            options={"temperature": kwargs.get("temperature", self.temperature)},
        )
        return response["message"]["content"]

    def chat_stream(self, messages: list[dict[str, str]], **kwargs) -> Generator[str, None, None]:
        client = self._get_client()
        stream = client.chat(
            model=kwargs.get("model", self.model),
            messages=messages,
            options={"temperature": kwargs.get("temperature", self.temperature)},
            stream=True,
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

    def list_models(self) -> list[dict]:
        """List all locally available Ollama models.

        Returns:
            List of dicts with 'name', 'size', and 'modified' keys.
            Returns an empty list if the server is unreachable.
        """
        try:
            client = self._get_client()
            result = client.list()

            # The ollama SDK may return:
            #   - A ListResponse object with a `.models` attribute  (newer SDK)
            #   - A plain dict with a "models" key                  (older SDK)
            #   - Directly iterable list                            (very old)
            if hasattr(result, "models"):
                model_list = result.models          # newer SDK: ListResponse
            elif isinstance(result, dict):
                model_list = result.get("models", [])
            else:
                model_list = list(result)           # fallback: already iterable

            models = []
            for model in model_list:
                if isinstance(model, dict):
                    name = model.get("name") or model.get("model", "unknown")
                    size = model.get("size", 0)
                    modified = model.get("modified_at", model.get("modified", ""))
                else:
                    # Newer ollama library returns objects with attributes.
                    # Primary key is `model` (e.g. "gemma4:12b"), fallback to `name`.
                    name = getattr(model, "model", None) or getattr(model, "name", "unknown") or "unknown"
                    size = getattr(model, "size", 0) or 0
                    modified = getattr(model, "modified_at", "")

                models.append({
                    "name": name,
                    "size": self._format_size(size) if isinstance(size, (int, float)) else str(size),
                    "modified": str(modified)[:10] if modified else "",
                })
            return models
        except Exception:
            return []


    def _format_size(self, size_bytes) -> str:
        """Format byte count into human-readable string."""
        if not size_bytes or not isinstance(size_bytes, (int, float)):
            return "unknown"
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def set_model(self, model: str) -> bool:
        """Switch to a different model. Verifies it exists first.

        Args:
            model: Model name to switch to.

        Returns:
            True if the model was found and set successfully.
        """
        available = [m["name"] for m in self.list_models()]
        # Match exact name
        if model in available:
            self.model = model
            return True
        # Match prefix (e.g., "mistral" matches "mistral:latest")
        matches = [m for m in available if model in m]
        if matches:
            self.model = matches[0]
            return True
        return False

    def is_available(self) -> bool:
        try:
            client = self._get_client()
            client.list()
            return True
        except Exception:
            return False

    def get_model_name(self) -> str:
        return f"{self.model} (local via Ollama)"
