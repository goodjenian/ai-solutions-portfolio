"""
DeepSeek model provider implementation.

Supports DeepSeek-V3 and other DeepSeek models via OpenAI-compatible API.
"""

import os
from typing import Any, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from .base import (
    ModelCapability,
    ModelInfo,
    PricingInfo,
    RemoteModelProvider,
)


class DeepSeekProvider(RemoteModelProvider):
    """DeepSeek model provider using OpenAI-compatible API."""

    @property
    def name(self) -> str:
        return "deepseek"

    @property
    def display_name(self) -> str:
        return "DeepSeek"

    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(config)
        # Get API key from config, environment, or None
        if "api_key" not in self.config:
            self.config["api_key"] = os.getenv("DEEPSEEK_API_KEY")

        # Set base URL for DeepSeek API
        if "base_url" not in self.config:
            self.config["base_url"] = "https://api.deepseek.com"

    def list_models(self) -> List[ModelInfo]:
        """List available DeepSeek models."""
        return [
            # Latest Models (2025)
            ModelInfo(
                id="deepseek-reasoner",
                display_name="DeepSeek R1 (Latest - Reasoning)",
                provider_name=self.display_name,
                context_window=64000,
                pricing=PricingInfo(input_price_per_1m=0.55, output_price_per_1m=2.19),
                capabilities=[
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE,
                    ModelCapability.SYSTEM_MESSAGES,
                ],
                description="Latest advanced reasoning model - competes with o1, shows chain-of-thought",
                recommended_for=[
                    "complex reasoning",
                    "math problems",
                    "scientific analysis",
                    "detailed explanations",
                ],
            ),
            ModelInfo(
                id="deepseek-chat",
                display_name="DeepSeek V3 Chat (Recommended)",
                provider_name=self.display_name,
                context_window=64000,
                pricing=PricingInfo(input_price_per_1m=0.14, output_price_per_1m=0.28),
                capabilities=[
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE,
                    ModelCapability.SYSTEM_MESSAGES,
                ],
                description="Latest general-purpose chat model (V3) - strong reasoning at low cost",
                recommended_for=[
                    "general chat",
                    "reasoning",
                    "coding assistance",
                    "cost-effective",
                ],
            ),
            ModelInfo(
                id="deepseek-coder",
                display_name="DeepSeek Coder",
                provider_name=self.display_name,
                context_window=64000,
                pricing=PricingInfo(input_price_per_1m=0.14, output_price_per_1m=0.28),
                capabilities=[
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE,
                    ModelCapability.SYSTEM_MESSAGES,
                ],
                description="Specialized coding model trained on code and technical documentation",
                recommended_for=[
                    "code generation",
                    "debugging",
                    "code review",
                    "technical documentation",
                ],
            ),
        ]

    def create_model(
        self,
        model_id: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        streaming: bool = True,
        request_timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Create DeepSeek model instance using OpenAI-compatible client."""
        # Validate model exists
        model_info = self.get_model_info(model_id)
        if not model_info:
            available = [m.id for m in self.list_models()]
            raise ValueError(
                f"Model '{model_id}' not available. Available models: {', '.join(available)}"
            )

        # Validate API key
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError(
                "DeepSeek API key required. "
                "Set DEEPSEEK_API_KEY environment variable or provide in config."
            )

        # Get timeout from config or use default from settings
        timeout = request_timeout
        if timeout is None:
            timeout = self.config.get("request_timeout")
        if timeout is None:
            from config.settings import get_settings

            timeout = get_settings().llm_request_timeout_seconds

        llm = ChatOpenAI(
            model=model_id,
            temperature=temperature,
            streaming=streaming,
            api_key=SecretStr(api_key),
            base_url=self.config.get("base_url", "https://api.deepseek.com"),
            request_timeout=timeout,  # type: ignore[call-arg]
            **kwargs,
        )
        if max_tokens is not None:
            llm.max_tokens = max_tokens
        return llm

    def validate_connection(self) -> tuple[bool, Optional[str]]:
        """Validate DeepSeek connection."""
        api_key = self.get_api_key()
        if not api_key:
            return False, "API key not provided"

        try:
            # Try to create a minimal model instance
            self.create_model("deepseek-chat")
            # If no error, connection is valid
            return True, None
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
