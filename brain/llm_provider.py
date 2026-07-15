"""Abstract LLM provider interface for V.E.R.A."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM backends (Mistral API, Ollama, etc.) must implement this interface.
    """

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            **kwargs: Additional provider-specific parameters.

        Returns:
            The assistant's response text.
        """
        ...

    @abstractmethod
    def chat_stream(self, messages: list[dict[str, str]], **kwargs):
        """Send a chat completion request with streaming response.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            **kwargs: Additional provider-specific parameters.

        Yields:
            Chunks of the assistant's response text.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available and ready.

        Returns:
            True if the provider is ready to accept requests.
        """
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name/identifier of the currently loaded model.

        Returns:
            Model name string.
        """
        ...
