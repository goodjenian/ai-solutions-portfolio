import logging

from fastapi import APIRouter, Header, HTTPException, Query

import models.user_model_preferences as user_model_preferences
from api.models import (
    ModelCatalogItem,
    ModelPreferences,
    ModelPreferencesUpdate,
    ModelPricing,
    ModelProviderCatalog,
    ModelRuntimeTestResponse,
    NotificationSettings,
)
from models.provider_factory import ModelProviderFactory
from notifications.notification_preferences import (
    AlertFrequency,
    AlertType,
    NotificationPreferencesManager,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Settings"])

PREFS_MANAGER = NotificationPreferencesManager()


def _resolve_user_email(user_email: str | None, x_user_email: str | None) -> str:
    resolved = (user_email or x_user_email or "").strip()
    if not resolved:
        raise HTTPException(status_code=400, detail="Missing user email")
    return resolved


@router.get("/settings/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    user_email: str | None = Query(default=None),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
):
    """Get notification settings for the current user."""
    try:
        resolved_user_email = _resolve_user_email(user_email, x_user_email)
        prefs = PREFS_MANAGER.get_preferences(resolved_user_email)

        # Map backend preferences to frontend model
        # Logic: if DIGEST is in enabled_alerts, email_digest is True
        email_digest = prefs.is_alert_enabled(AlertType.DIGEST)

        frequency = "weekly"
        if prefs.alert_frequency == AlertFrequency.DAILY:
            frequency = "daily"
        elif prefs.alert_frequency == AlertFrequency.WEEKLY:
            frequency = "weekly"

        return NotificationSettings(
            email_digest=email_digest,
            frequency=frequency,
            expert_mode=getattr(prefs, "expert_mode", False),
            marketing_emails=getattr(prefs, "marketing_emails", False),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/settings/notifications", response_model=NotificationSettings)
async def update_notification_settings(
    settings: NotificationSettings,
    user_email: str | None = Query(default=None),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
):
    """Update notification settings for the current user."""
    try:
        resolved_user_email = _resolve_user_email(user_email, x_user_email)
        prefs = PREFS_MANAGER.get_preferences(resolved_user_email)

        # Update fields
        if settings.email_digest:
            prefs.enabled_alerts.add(AlertType.DIGEST)
        else:
            prefs.enabled_alerts.discard(AlertType.DIGEST)

        # Map frequency
        if settings.frequency == "daily":
            prefs.alert_frequency = AlertFrequency.DAILY
        else:
            prefs.alert_frequency = AlertFrequency.WEEKLY

        prefs.expert_mode = settings.expert_mode
        prefs.marketing_emails = settings.marketing_emails

        PREFS_MANAGER.save_preferences(prefs)

        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/settings/models", response_model=list[ModelProviderCatalog])
async def list_model_catalog():
    """List available model providers and their models."""
    try:
        providers: list[ModelProviderCatalog] = []
        for provider_name in ModelProviderFactory.list_providers():
            provider = ModelProviderFactory.get_provider(provider_name)
            models: list[ModelCatalogItem] = []
            runtime_available: bool | None = None
            available_models: list[str] | None = None
            runtime_error: str | None = None

            for model_info in provider.list_models():
                pricing = None
                if model_info.pricing:
                    pricing = ModelPricing(
                        input_price_per_1m=model_info.pricing.input_price_per_1m,
                        output_price_per_1m=model_info.pricing.output_price_per_1m,
                        currency=model_info.pricing.currency,
                    )

                models.append(
                    ModelCatalogItem(
                        id=model_info.id,
                        display_name=model_info.display_name,
                        provider_name=model_info.provider_name,
                        context_window=model_info.context_window,
                        pricing=pricing,
                        capabilities=[c.value for c in model_info.capabilities],
                        description=model_info.description,
                        recommended_for=model_info.recommended_for,
                    )
                )

            if provider.is_local:
                runtime_available, runtime_error = provider.validate_connection()
                if runtime_available and hasattr(provider, "list_available_models"):
                    maybe_models = provider.list_available_models()
                    available_models = list(maybe_models) if maybe_models else []
                else:
                    available_models = []

            providers.append(
                ModelProviderCatalog(
                    name=provider.name,
                    display_name=provider.display_name,
                    is_local=provider.is_local,
                    requires_api_key=provider.requires_api_key,
                    models=models,
                    runtime_available=runtime_available,
                    available_models=available_models,
                    runtime_error=runtime_error,
                )
            )
        return providers
    except Exception as e:
        logger.error(f"Error listing model catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/settings/test-runtime", response_model=ModelRuntimeTestResponse)
async def test_runtime(provider: str = Query(...)):
    """
    Test connection/runtime status for a specific provider.
    """
    try:
        allowed_providers = set(ModelProviderFactory.list_providers())
        if provider not in allowed_providers:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

        p = ModelProviderFactory.get_provider(provider)
        if not p.is_local:
            raise HTTPException(
                status_code=400, detail=f"Provider '{provider}' is not a local runtime provider"
            )

        runtime_available, runtime_error = p.validate_connection()
        available_models = []
        if runtime_available and hasattr(p, "list_available_models"):
            maybe_models = p.list_available_models()
            available_models = list(maybe_models) if maybe_models else []

        return ModelRuntimeTestResponse(
            provider=provider,
            is_local=True,
            runtime_available=runtime_available,
            available_models=available_models,
            runtime_error=runtime_error,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing runtime: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/settings/model-preferences", response_model=ModelPreferences)
async def get_model_preferences(
    user_email: str | None = Query(default=None),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
):
    try:
        resolved_user_email = _resolve_user_email(user_email, x_user_email)
        prefs = user_model_preferences.MODEL_PREFS_MANAGER.get_preferences(resolved_user_email)
        return ModelPreferences(
            preferred_provider=prefs.preferred_provider,
            preferred_model=prefs.preferred_model,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error fetching model preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/settings/model-preferences", response_model=ModelPreferences)
async def update_model_preferences(
    payload: ModelPreferencesUpdate,
    user_email: str | None = Query(default=None),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
):
    try:
        resolved_user_email = _resolve_user_email(user_email, x_user_email)
        existing = user_model_preferences.MODEL_PREFS_MANAGER.get_preferences(resolved_user_email)

        incoming_provider = payload.preferred_provider
        incoming_model = payload.preferred_model

        next_provider = (
            incoming_provider if incoming_provider is not None else existing.preferred_provider
        )
        next_model = incoming_model if incoming_model is not None else existing.preferred_model

        if incoming_provider is not None and (incoming_provider.strip() == ""):
            next_provider = None
            if incoming_model is None:
                next_model = None

        if incoming_model is not None and (incoming_model.strip() == ""):
            next_model = None

        if next_model and not next_provider:
            raise HTTPException(
                status_code=400,
                detail="preferred_provider is required when setting preferred_model",
            )

        if next_provider:
            allowed_providers = set(ModelProviderFactory.list_providers())
            if next_provider not in allowed_providers:
                raise HTTPException(status_code=400, detail=f"Unknown provider: {next_provider}")

            provider = ModelProviderFactory.get_provider(next_provider)
            if next_model:
                allowed_models = {m.id for m in provider.list_models()}
                if next_model not in allowed_models:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown model for provider '{next_provider}': {next_model}",
                    )
            else:
                if incoming_provider is not None and existing.preferred_model:
                    allowed_models = {m.id for m in provider.list_models()}
                    if existing.preferred_model in allowed_models:
                        next_model = existing.preferred_model

        updated = user_model_preferences.MODEL_PREFS_MANAGER.update_preferences(
            resolved_user_email,
            preferred_provider=next_provider,
            preferred_model=next_model,
        )

        return ModelPreferences(
            preferred_provider=updated.preferred_provider,
            preferred_model=updated.preferred_model,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error updating model preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
