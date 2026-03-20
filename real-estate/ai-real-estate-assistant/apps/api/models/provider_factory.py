"""
Model provider factory for creating and managing LLM providers.

This module provides a unified interface for accessing different model providers
and their models.
"""

import logging
from typing import Any, Dict, List, Optional, Type

from langchain_core.language_models import BaseChatModel

from config.settings import settings

from .providers.anthropic import AnthropicProvider
from .providers.base import ModelInfo, ModelProvider
from .providers.deepseek import DeepSeekProvider
from .providers.google import GoogleProvider
from .providers.grok import GrokProvider
from .providers.ollama import OllamaProvider
from .providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)


class ModelProviderFactory:
    """
    Factory for creating and managing model providers.

    This class provides a centralized way to access all available providers
    and their models.
    """

    # Registry of available providers
    _PROVIDERS: Dict[str, Type[ModelProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "grok": GrokProvider,
        "deepseek": DeepSeekProvider,
        "ollama": OllamaProvider,
    }

    # Cache of instantiated providers
    _instances: Dict[str, ModelProvider] = {}

    @classmethod
    def list_providers(cls) -> List[str]:
        """
        List all available provider names.

        Returns:
            List of provider names (e.g., ['openai', 'anthropic', ...])
        """
        return list(cls._PROVIDERS.keys())

    @classmethod
    def get_provider(
        cls, provider_name: str, config: Optional[Dict[str, Any]] = None, use_cache: bool = True
    ) -> ModelProvider:
        """
        Get a provider instance by name.

        Args:
            provider_name: Name of the provider (e.g., 'openai', 'anthropic')
            config: Optional configuration dictionary
            use_cache: Whether to use cached instances (default: True)

        Returns:
            ModelProvider instance

        Raises:
            ValueError: If provider_name is not recognized
        """
        if provider_name not in cls._PROVIDERS:
            available = ", ".join(cls.list_providers())
            raise ValueError(
                f"Unknown provider '{provider_name}'. Available providers: {available}"
            )

        # Check cache
        if use_cache and provider_name in cls._instances:
            # If config is provided, we might want to update the cached instance or create a new one.
            # For now, we assume cached instances are reused unless explicit new config is needed.
            # If config is passed, we skip cache to ensure config is applied.
            if config is None:
                return cls._instances[provider_name]

        # Prepare config with defaults from settings
        if config is None:
            config = {}

        # Inject API key from settings if not present
        if "api_key" not in config:
            if provider_name == "openai":
                config["api_key"] = settings.openai_api_key
            elif provider_name == "anthropic":
                config["api_key"] = settings.anthropic_api_key
            elif provider_name == "google":
                config["api_key"] = settings.google_api_key
            elif provider_name == "grok":
                config["api_key"] = settings.grok_api_key
            elif provider_name == "deepseek":
                config["api_key"] = settings.deepseek_api_key

        # Create new instance
        provider_class = cls._PROVIDERS[provider_name]
        provider = provider_class(config=config)

        # Cache if requested
        if use_cache:
            cls._instances[provider_name] = provider

        return provider

    @classmethod
    def list_all_models(cls, include_unavailable: bool = True) -> List[ModelInfo]:
        """
        List all available models from all providers.

        Args:
            include_unavailable: Whether to include models from providers
                                 with connection issues

        Returns:
            List of ModelInfo objects from all providers
        """
        all_models = []

        for provider_name in cls.list_providers():
            try:
                # Use cached provider (will use settings API keys)
                provider = cls.get_provider(provider_name)

                # Check connection if requested
                if not include_unavailable:
                    is_valid, error = provider.validate_connection()
                    if not is_valid:
                        continue

                models = provider.list_models()
                all_models.extend(models)

            except Exception as e:
                logger.warning("Could not load models from %s: %s", provider_name, e)
                continue

        return all_models

    @classmethod
    def get_model_by_id(cls, model_id: str) -> Optional[tuple[ModelProvider, ModelInfo]]:
        """
        Find a model by its ID across all providers.

        Args:
            model_id: Model identifier (e.g., 'gpt-4o', 'claude-3-5-sonnet-20241022')

        Returns:
            Tuple of (provider, model_info) if found, None otherwise
        """
        for provider_name in cls.list_providers():
            try:
                provider = cls.get_provider(provider_name)
                model_info = provider.get_model_info(model_id)

                if model_info:
                    return provider, model_info

            except Exception:
                continue

        return None

    @classmethod
    def create_model(
        cls,
        model_id: str,
        provider_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: bool = True,
        **kwargs: Any,
    ) -> BaseChatModel:
        """
        Create a model instance by ID.

        Args:
            model_id: Model identifier
            provider_name: Optional provider name (auto-detected if not provided)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            streaming: Whether to enable streaming
            **kwargs: Additional model-specific parameters

        Returns:
            Configured LangChain chat model instance

        Raises:
            ValueError: If model not found or provider not available
        """
        # Apply defaults from settings if not provided
        if temperature is None:
            temperature = settings.default_temperature

        if max_tokens is None:
            max_tokens = settings.default_max_tokens

        # If provider specified, use it directly
        if provider_name:
            provider = cls.get_provider(provider_name)
            return provider.create_model(
                model_id=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                **kwargs,
            )

        # Auto-detect provider
        result = cls.get_model_by_id(model_id)
        if not result:
            raise ValueError(
                f"Model '{model_id}' not found in any provider. "
                f"Available providers: {', '.join(cls.list_providers())}"
            )

        provider, model_info = result
        return provider.create_model(
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
            **kwargs,
        )

    @classmethod
    def get_available_providers(cls) -> List[tuple[str, bool, Optional[str]]]:
        """
        Get list of providers with their availability status.

        Returns:
            List of tuples: (provider_name, is_available, error_message)
        """
        results = []

        for provider_name in cls.list_providers():
            try:
                provider = cls.get_provider(provider_name)
                is_valid, error = provider.validate_connection()
                results.append((provider_name, is_valid, error))

            except Exception as e:
                results.append((provider_name, False, str(e)))

        return results

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[ModelProvider]) -> None:
        """
        Register a custom provider.

        Args:
            name: Provider name
            provider_class: Provider class (must inherit from ModelProvider)
        """
        if not issubclass(provider_class, ModelProvider):
            raise TypeError("Provider class must inherit from ModelProvider")

        cls._PROVIDERS[name] = provider_class

        # Clear cache for this provider if it exists
        if name in cls._instances:
            del cls._instances[name]
        return None

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached provider instances."""
        cls._instances.clear()
        return None


def get_model_display_info(model_info: ModelInfo) -> Dict[str, Any]:
    """
    Get formatted display information for a model.

    Args:
        model_info: ModelInfo object

    Returns:
        Dictionary with formatted display information
    """
    info = {
        "name": model_info.display_name,
        "id": model_info.id,
        "provider": model_info.provider_name,
        "context": f"{model_info.context_window:,} tokens",
        "capabilities": [c.value for c in model_info.capabilities],
    }

    if model_info.pricing:
        info["cost"] = (
            f"${model_info.pricing.input_price_per_1m:.2f} / "
            f"${model_info.pricing.output_price_per_1m:.2f} per 1M tokens"
        )
    else:
        info["cost"] = "Free (local)"

    if model_info.description:
        info["description"] = model_info.description

    if model_info.recommended_for:
        info["recommended_for"] = model_info.recommended_for

    return info
