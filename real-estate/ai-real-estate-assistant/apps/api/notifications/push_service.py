"""Web Push notification service (Task #63).

Provides functionality for sending web push notifications to users
via the Web Push protocol using VAPID authentication.
"""

import json
import logging
from typing import Any, Optional

from pywebpush import WebPushException, webpush

from config.settings import get_settings
from db.models import PushSubscription

logger = logging.getLogger(__name__)

settings = get_settings()


class PushNotificationPayload:
    """Payload for a push notification."""

    def __init__(
        self,
        title: str,
        body: str,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        url: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ):
        """Initialize push notification payload.

        Args:
            title: Notification title
            body: Notification body text
            icon: Optional icon URL
            badge: Optional badge URL
            url: Optional URL to open on click
            data: Optional additional data
        """
        self.title = title
        self.body = body
        self.icon = icon
        self.badge = badge
        self.url = url
        self.data = data or {}

    def to_json(self) -> str:
        """Convert to JSON string for push."""
        payload = {
            "title": self.title,
            "body": self.body,
            "icon": self.icon or "/icon-192x192.png",
            "badge": self.badge or "/icon-192x192.png",
            "data": {
                **self.data,
                "url": self.url,
            },
        }
        return json.dumps(payload)


class PushNotificationService:
    """Service for sending web push notifications."""

    def __init__(
        self,
        vapid_private_key: Optional[str] = None,
        vapid_public_key: Optional[str] = None,
        vapid_subject: Optional[str] = None,
    ):
        """Initialize the push notification service.

        Args:
            vapid_private_key: VAPID private key (defaults to settings)
            vapid_public_key: VAPID public key (defaults to settings)
            vapid_subject: VAPID subject (defaults to settings)
        """
        self.vapid_private_key = vapid_private_key or settings.vapid_private_key
        self.vapid_public_key = vapid_public_key or settings.vapid_public_key
        self.vapid_subject = vapid_subject or settings.vapid_subject

        self.enabled = bool(
            settings.push_enabled and self.vapid_private_key and self.vapid_public_key
        )

        if not self.enabled:
            logger.warning("Push notifications disabled: missing VAPID keys or PUSH_ENABLED=false")

    def _get_subscription_info(self, subscription: PushSubscription) -> dict[str, Any]:
        """Convert PushSubscription model to webpush format.

        Args:
            subscription: Database model instance

        Returns:
            Dict with endpoint and keys for pywebpush
        """
        return {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        }

    async def send_notification(
        self,
        subscription: PushSubscription,
        payload: PushNotificationPayload,
        ttl: int = 86400,  # 24 hours
    ) -> bool:
        """Send a push notification to a single subscription.

        Args:
            subscription: PushSubscription database model
            payload: Notification payload
            ttl: Time-to-live in seconds (default 24 hours)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Push notifications not enabled, skipping send")
            return False

        if not subscription.is_active:
            logger.debug("Subscription %s is inactive, skipping", subscription.id)
            return False

        try:
            subscription_info = self._get_subscription_info(subscription)

            webpush(
                subscription_info=subscription_info,
                data=payload.to_json(),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": self.vapid_subject,
                },
                ttl=ttl,
            )

            logger.debug(
                "Sent push notification to subscription %s: %s",
                subscription.id,
                payload.title,
            )
            return True

        except WebPushException as e:
            # Handle common errors
            if e.response and e.response.status_code == 410:
                # Subscription has expired or been unsubscribed
                logger.info(
                    "Push subscription %s has expired (410 Gone)",
                    subscription.id,
                )
            else:
                logger.error(
                    "Failed to send push to subscription %s: %s",
                    subscription.id,
                    str(e),
                )
            return False

        except Exception:
            logger.exception(
                "Unexpected error sending push to subscription %s",
                subscription.id,
            )
            return False

    async def send_to_subscriptions(
        self,
        subscriptions: list[PushSubscription],
        payload: PushNotificationPayload,
        ttl: int = 86400,
    ) -> tuple[int, int]:
        """Send a push notification to multiple subscriptions.

        Args:
            subscriptions: List of PushSubscription models
            payload: Notification payload
            ttl: Time-to-live in seconds

        Returns:
            Tuple of (success_count, failure_count)
        """
        if not self.enabled:
            logger.warning("Push notifications not enabled, skipping batch send")
            return (0, len(subscriptions))

        success_count = 0
        failure_count = 0

        for subscription in subscriptions:
            success = await self.send_notification(subscription, payload, ttl)
            if success:
                success_count += 1
            else:
                failure_count += 1

        logger.info(
            "Batch push send complete: %d success, %d failed",
            success_count,
            failure_count,
        )
        return (success_count, failure_count)

    async def send_price_drop_notification(
        self,
        subscriptions: list[PushSubscription],
        property_address: str,
        old_price: float,
        new_price: float,
        currency: str,
        property_url: Optional[str] = None,
    ) -> tuple[int, int]:
        """Send a price drop notification to multiple subscriptions.

        Args:
            subscriptions: List of user's subscriptions
            property_address: Property address
            old_price: Previous price
            new_price: New price
            currency: Currency code
            property_url: Optional property detail URL

        Returns:
            Tuple of (success_count, failure_count)
        """
        price_diff = old_price - new_price
        percent_drop = (price_diff / old_price) * 100 if old_price > 0 else 0

        body = (
            f"Price dropped from {old_price:,.0f} {currency} to {new_price:,.0f} {currency} "
            f"(-{percent_drop:.1f}%)"
        )

        payload = PushNotificationPayload(
            title=f"Price Drop: {property_address[:50]}...",
            body=body,
            url=property_url,
            data={
                "type": "price_drop",
                "property_address": property_address,
                "old_price": old_price,
                "new_price": new_price,
                "currency": currency,
            },
        )

        return await self.send_to_subscriptions(subscriptions, payload)

    async def send_new_property_notification(
        self,
        subscriptions: list[PushSubscription],
        property_address: str,
        price: float,
        currency: str,
        property_url: Optional[str] = None,
    ) -> tuple[int, int]:
        """Send a new property notification to multiple subscriptions.

        Args:
            subscriptions: List of user's subscriptions
            property_address: Property address
            price: Property price
            currency: Currency code
            property_url: Optional property detail URL

        Returns:
            Tuple of (success_count, failure_count)
        """
        payload = PushNotificationPayload(
            title=f"New Property: {property_address[:50]}...",
            body=f"New listing available at {price:,.0f} {currency}",
            url=property_url,
            data={
                "type": "new_property",
                "property_address": property_address,
                "price": price,
                "currency": currency,
            },
        )

        return await self.send_to_subscriptions(subscriptions, payload)

    async def send_market_anomaly_notification(
        self,
        subscriptions: list[PushSubscription],
        anomaly_type: str,
        location: str,
        severity: str,
        details: str,
        anomaly_url: Optional[str] = None,
    ) -> tuple[int, int]:
        """Send a market anomaly notification to multiple subscriptions.

        Args:
            subscriptions: List of user's subscriptions
            anomaly_type: Type of anomaly (price_spike, price_drop, etc.)
            location: Affected location
            severity: Anomaly severity (low, medium, high, critical)
            details: Brief description
            anomaly_url: Optional URL for more details

        Returns:
            Tuple of (success_count, failure_count)
        """
        emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "📊",
            "low": "📈",
        }.get(severity, "📊")

        payload = PushNotificationPayload(
            title=f"{emoji} Market Alert: {location}",
            body=details[:200],
            url=anomaly_url,
            data={
                "type": "market_anomaly",
                "anomaly_type": anomaly_type,
                "location": location,
                "severity": severity,
            },
        )

        return await self.send_to_subscriptions(subscriptions, payload)


# Global service instance
_push_service: Optional[PushNotificationService] = None


def get_push_service() -> PushNotificationService:
    """Get or create the global push notification service.

    Returns:
        PushNotificationService instance
    """
    global _push_service
    if _push_service is None:
        _push_service = PushNotificationService()
    return _push_service
