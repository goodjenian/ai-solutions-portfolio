"""
Notification system for email alerts and updates.

Provides email notifications for:
- Price drops
- New property matches
- Saved search alerts
- Market updates
- Daily/weekly digests
"""

from .alert_manager import Alert, AlertManager, AlertType
from .email_service import (
    EmailConfig,
    EmailProvider,
    EmailSendError,
    EmailService,
    EmailServiceFactory,
    EmailValidationError,
)
from .email_templates import (
    DigestTemplate,
    EmailTemplate,
    MarketUpdateTemplate,
    NewPropertyTemplate,
    PriceDropTemplate,
    TestEmailTemplate,
)
from .notification_history import (
    NotificationHistory,
    NotificationRecord,
    NotificationStatus,
    NotificationType,
)
from .notification_preferences import (
    AlertFrequency,
    DigestDay,
    NotificationPreferences,
    NotificationPreferencesManager,
    create_default_preferences,
)

__all__ = [
    # Email Service
    "EmailService",
    "EmailConfig",
    "EmailProvider",
    "EmailServiceFactory",
    "EmailValidationError",
    "EmailSendError",
    # Alert Manager
    "AlertManager",
    "AlertType",
    "Alert",
    # Notification Preferences
    "NotificationPreferences",
    "NotificationPreferencesManager",
    "AlertFrequency",
    "DigestDay",
    "create_default_preferences",
    # Email Templates
    "EmailTemplate",
    "PriceDropTemplate",
    "NewPropertyTemplate",
    "DigestTemplate",
    "TestEmailTemplate",
    "MarketUpdateTemplate",
    # Notification History
    "NotificationHistory",
    "NotificationRecord",
    "NotificationStatus",
    "NotificationType",
]
