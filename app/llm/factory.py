from typing import Optional
import os
import logging

from .base import BaseLLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider

logger = logging.getLogger(__name__)

# Global provider instance
_provider: Optional[BaseLLMProvider] = None


def create_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> BaseLLMProvider:
    """Create an LLM provider instance.

    Args:
        provider_name: Name of the provider ('anthropic', 'openai', 'groq')
        api_key: API key (optional, will use env var if not provided)
        model: Model name (optional, will use provider default)

    Returns:
        An LLM provider instance

    Raises:
        ValueError: If provider name is unknown or API key is missing
    """
    provider_name = provider_name.lower()

    if provider_name == "anthropic":
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        return AnthropicProvider(api_key=key, model=model)

    elif provider_name == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not found")
        return OpenAIProvider(api_key=key, model=model)

    elif provider_name == "groq":
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY not found")
        return GroqProvider(api_key=key, model=model)

    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")


def get_provider() -> BaseLLMProvider:
    """Get the global LLM provider instance.

    Creates the provider on first call based on LLM_PROVIDER env var.

    Returns:
        The global LLM provider instance
    """
    global _provider

    if _provider is None:
        provider_name = os.getenv("LLM_PROVIDER", "anthropic")
        model = os.getenv("LLM_MODEL")

        logger.info(f"Initializing LLM provider: {provider_name}")
        _provider = create_provider(provider_name, model=model)

    return _provider


def reset_provider() -> None:
    """Reset the global provider (useful for testing)."""
    global _provider
    _provider = None
