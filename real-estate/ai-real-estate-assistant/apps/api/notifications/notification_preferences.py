"""
Notification preferences management.

Handles:
- User notification preferences (frequency, alert types, thresholds)
- Quiet hours enforcement
- Alert frequency control (instant, daily, weekly)
- Per-search notification settings
"""

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from analytics import MarketInsights
from notifications.alert_manager import AlertManager, AlertType
from notifications.email_service import EmailService
from notifications.notification_history import (
    NotificationHistory,
    NotificationStatus,
    NotificationType,
)
from utils.property_cache import load_collection, load_previous_collection
from utils.saved_searches import SavedSearchManager

logger = logging.getLogger(__name__)


class AlertFrequency(str, Enum):
    """Alert delivery frequency options."""

    INSTANT = "instant"  # Send immediately when triggered
    HOURLY = "hourly"  # Batch and send hourly
    DAILY = "daily"  # Daily digest at specified time
    WEEKLY = "weekly"  # Weekly digest on specified day


class DigestDay(str, Enum):
    """Days of week for weekly digests."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


@dataclass
class NotificationPreferences:
    """
    User notification preferences.

    Attributes:
        user_email: User's email address
        alert_frequency: How often to send alerts
        enabled_alerts: Types of alerts user wants to receive
        price_drop_threshold: Minimum % price drop to trigger alert (default 5%)
        quiet_hours_start: Start of quiet hours (no alerts sent)
        quiet_hours_end: End of quiet hours
        daily_digest_time: Time to send daily digest (24-hour format)
        weekly_digest_day: Day to send weekly digest
        max_alerts_per_day: Maximum alerts to send per day
        per_search_settings: Custom settings for specific saved searches
        enabled: Whether notifications are enabled at all
    """

    user_email: str
    alert_frequency: AlertFrequency = AlertFrequency.INSTANT
    enabled_alerts: Set[AlertType] = field(
        default_factory=lambda: {
            AlertType.PRICE_DROP,
            AlertType.NEW_PROPERTY,
            AlertType.SAVED_SEARCH_MATCH,
        }
    )
    price_drop_threshold: float = 5.0  # Minimum % drop
    quiet_hours_start: Optional[str] = "22:00"  # 10 PM
    quiet_hours_end: Optional[str] = "08:00"  # 8 AM
    daily_digest_time: str = "09:00"  # 9 AM
    weekly_digest_day: DigestDay = DigestDay.MONDAY
    max_alerts_per_day: int = 10
    per_search_settings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    enabled: bool = True
    expert_mode: bool = False
    marketing_emails: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary for serialization."""
        data = asdict(self)
        # Convert sets to lists for JSON serialization
        data["enabled_alerts"] = [alert.value for alert in self.enabled_alerts]
        data["alert_frequency"] = self.alert_frequency.value
        data["weekly_digest_day"] = self.weekly_digest_day.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationPreferences":
        """Create preferences from dictionary."""
        # Convert alert types back to set
        if "enabled_alerts" in data:
            data["enabled_alerts"] = {AlertType(a) for a in data["enabled_alerts"]}

        # Convert enums
        if "alert_frequency" in data:
            data["alert_frequency"] = AlertFrequency(data["alert_frequency"])

        if "weekly_digest_day" in data:
            data["weekly_digest_day"] = DigestDay(data["weekly_digest_day"])

        # Convert datetime strings
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return cls(**data)

    def is_alert_enabled(self, alert_type: AlertType) -> bool:
        """Check if a specific alert type is enabled."""
        return self.enabled and alert_type in self.enabled_alerts

    def is_in_quiet_hours(self, check_time: Optional[datetime] = None) -> bool:
        """
        Check if current time is in quiet hours.

        Args:
            check_time: Time to check (defaults to now)

        Returns:
            True if in quiet hours
        """
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        if check_time is None:
            check_time = datetime.now()

        current_time = check_time.time()
        start = datetime.strptime(self.quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(self.quiet_hours_end, "%H:%M").time()

        # Handle quiet hours that span midnight
        if start <= end:
            return start <= current_time <= end
        else:
            return current_time >= start or current_time <= end

    def should_send_alert(
        self,
        alert_type: AlertType,
        alerts_sent_today: int = 0,
        check_time: Optional[datetime] = None,
    ) -> bool:
        """
        Determine if an alert should be sent based on preferences.

        Args:
            alert_type: Type of alert to send
            alerts_sent_today: Number of alerts already sent today
            check_time: Time to check (defaults to now)

        Returns:
            True if alert should be sent
        """
        # Check if notifications enabled
        if not self.enabled:
            return False

        if alert_type != AlertType.DIGEST and not self.is_alert_enabled(alert_type):
            return False

        if alert_type == AlertType.DIGEST and self.alert_frequency not in {
            AlertFrequency.DAILY,
            AlertFrequency.WEEKLY,
        }:
            return False

        # Respect quiet hours only for non-instant delivery modes
        if self.alert_frequency != AlertFrequency.INSTANT and self.is_in_quiet_hours(check_time):
            return False

        # Check daily limit
        if alerts_sent_today >= self.max_alerts_per_day:
            return False

        # For digest alerts, check if it's time
        if alert_type == AlertType.DIGEST:
            if self.alert_frequency == AlertFrequency.WEEKLY:
                # Check if today is the digest day
                if check_time is None:
                    check_time = datetime.now()
                current_day = check_time.strftime("%A").lower()
                return current_day == self.weekly_digest_day.value

        return True

    def get_search_preferences(self, search_id: str) -> Dict[str, Any]:
        """
        Get preferences for a specific saved search.

        Args:
            search_id: ID of the saved search

        Returns:
            Dictionary of search-specific preferences
        """
        return self.per_search_settings.get(search_id, {})

    def set_search_preferences(
        self,
        search_id: str,
        enabled: Optional[bool] = None,
        alert_frequency: Optional[AlertFrequency] = None,
        price_threshold: Optional[float] = None,
    ):
        """
        Set preferences for a specific saved search.

        Args:
            search_id: ID of the saved search
            enabled: Whether alerts are enabled for this search
            alert_frequency: Custom frequency for this search
            price_threshold: Custom price drop threshold
        """
        if search_id not in self.per_search_settings:
            self.per_search_settings[search_id] = {}

        if enabled is not None:
            self.per_search_settings[search_id]["enabled"] = enabled

        if alert_frequency is not None:
            self.per_search_settings[search_id]["alert_frequency"] = alert_frequency.value

        if price_threshold is not None:
            self.per_search_settings[search_id]["price_threshold"] = price_threshold

        self.updated_at = datetime.now()


class NotificationPreferencesManager:
    """
    Manager for storing and retrieving notification preferences.

    Handles persistence of user preferences to disk.
    """

    def __init__(self, storage_path: str = ".preferences"):
        """
        Initialize preferences manager.

        Args:
            storage_path: Directory to store preference files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        self.preferences_file = self.storage_path / "notification_preferences.json"
        self._preferences_cache: Dict[str, NotificationPreferences] = {}

        self._load_all_preferences()

    def get_preferences(self, user_email: str) -> NotificationPreferences:
        """
        Get preferences for a user.

        Args:
            user_email: User's email address

        Returns:
            User's notification preferences (creates defaults if not found)
        """
        if user_email not in self._preferences_cache:
            # Create default preferences
            prefs = NotificationPreferences(user_email=user_email)
            self._preferences_cache[user_email] = prefs
            self.save_preferences(prefs)

        return self._preferences_cache[user_email]

    def save_preferences(self, preferences: NotificationPreferences):
        """
        Save user preferences.

        Args:
            preferences: Preferences to save
        """
        preferences.updated_at = datetime.now()
        self._preferences_cache[preferences.user_email] = preferences
        self._save_all_preferences()

    def update_preferences(self, user_email: str, **kwargs) -> NotificationPreferences:
        """
        Update specific preference fields for a user.

        Args:
            user_email: User's email address
            **kwargs: Fields to update

        Returns:
            Updated preferences
        """
        prefs = self.get_preferences(user_email)

        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        prefs.updated_at = datetime.now()
        self.save_preferences(prefs)

        return prefs

    def delete_preferences(self, user_email: str):
        """
        Delete preferences for a user.

        Args:
            user_email: User's email address
        """
        if user_email in self._preferences_cache:
            del self._preferences_cache[user_email]
            self._save_all_preferences()

    def get_all_preferences(self) -> List[NotificationPreferences]:
        """
        Get preferences for all users.

        Returns:
            List of all user preferences
        """
        return list(self._preferences_cache.values())

    def get_users_by_frequency(self, frequency: AlertFrequency) -> List[NotificationPreferences]:
        """
        Get all users with a specific alert frequency.

        Args:
            frequency: Alert frequency to filter by

        Returns:
            List of user preferences matching frequency
        """
        return [
            prefs
            for prefs in self._preferences_cache.values()
            if prefs.alert_frequency == frequency and prefs.enabled
        ]

    def get_users_with_alert_enabled(self, alert_type: AlertType) -> List[NotificationPreferences]:
        """
        Get all users who have a specific alert type enabled.

        Args:
            alert_type: Type of alert

        Returns:
            List of user preferences with alert enabled
        """
        return [
            prefs
            for prefs in self._preferences_cache.values()
            if prefs.is_alert_enabled(alert_type)
        ]

    def _load_all_preferences(self):
        """Load all preferences from disk."""
        if not self.preferences_file.exists():
            return

        try:
            with open(self.preferences_file, "r") as f:
                data = json.load(f)

            for user_email, prefs_data in data.items():
                prefs = NotificationPreferences.from_dict(prefs_data)
                self._preferences_cache[user_email] = prefs

        except Exception as e:
            logger.warning("Error loading preferences: %s", e)

    def _save_all_preferences(self):
        """Save all preferences to disk."""
        data = {email: prefs.to_dict() for email, prefs in self._preferences_cache.items()}

        with open(self.preferences_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about notification preferences.

        Returns:
            Dictionary with preference statistics
        """
        total_users = len(self._preferences_cache)
        enabled_users = sum(1 for p in self._preferences_cache.values() if p.enabled)

        frequency_counts = {}
        for freq in AlertFrequency:
            frequency_counts[freq.value] = len(self.get_users_by_frequency(freq))

        alert_type_counts = {}
        for alert_type in AlertType:
            alert_type_counts[alert_type.value] = len(self.get_users_with_alert_enabled(alert_type))

        return {
            "total_users": total_users,
            "enabled_users": enabled_users,
            "disabled_users": total_users - enabled_users,
            "by_frequency": frequency_counts,
            "by_alert_type": alert_type_counts,
        }


def create_default_preferences(user_email: str) -> NotificationPreferences:
    """
    Create default notification preferences for a new user.

    Args:
        user_email: User's email address

    Returns:
        Default NotificationPreferences
    """
    return NotificationPreferences(
        user_email=user_email,
        alert_frequency=AlertFrequency.DAILY,
        enabled_alerts={
            AlertType.PRICE_DROP,
            AlertType.NEW_PROPERTY,
            AlertType.SAVED_SEARCH_MATCH,
        },
        price_drop_threshold=5.0,
        quiet_hours_start="22:00",
        quiet_hours_end="08:00",
        daily_digest_time="09:00",
        weekly_digest_day=DigestDay.MONDAY,
        max_alerts_per_day=10,
        enabled=True,
    )


class DigestScheduler:
    def __init__(
        self,
        email_service: EmailService,
        prefs_manager: Optional[NotificationPreferencesManager] = None,
        history: Optional[NotificationHistory] = None,
        search_manager: Optional[SavedSearchManager] = None,
        poll_interval_seconds: int = 30,
        storage_path_alerts: str = ".alerts",
    ):
        self._email_service = email_service
        self._prefs_manager = prefs_manager or NotificationPreferencesManager()
        self._history = history or NotificationHistory()
        self._search_manager = search_manager or SavedSearchManager()
        self._poll_interval_seconds = poll_interval_seconds
        self._storage_path_alerts = storage_path_alerts

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_attempt_minute: Dict[tuple[str, NotificationType], str] = {}

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="DigestScheduler")
        self._thread.start()

    def stop(self, timeout_seconds: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout_seconds)

    def run_pending(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        check_time = now or datetime.now()
        sent = {"daily": 0, "weekly": 0}
        errors: List[str] = []

        try:
            self._refresh_data_sources()
            sent["daily"] += self._send_due(AlertFrequency.DAILY, check_time)
            sent["weekly"] += self._send_due(AlertFrequency.WEEKLY, check_time)
        except Exception as e:
            errors.append(str(e))

        return {"sent": sent, "errors": errors}

    def _refresh_data_sources(self) -> None:
        try:
            self._prefs_manager._load_all_preferences()
        except Exception:
            pass

        try:
            self._search_manager.saved_searches = self._search_manager._load_searches()
        except Exception:
            pass

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self.run_pending()
            self._stop_event.wait(self._poll_interval_seconds)

    def _send_due(self, frequency: AlertFrequency, now: datetime) -> int:
        sent_count = 0
        am = AlertManager(email_service=self._email_service, storage_path=self._storage_path_alerts)
        users = self._prefs_manager.get_users_by_frequency(frequency)
        for prefs in users:
            record_id: Optional[str] = None
            try:
                if not self._is_time_match(prefs, now, frequency):
                    continue
                if not prefs.should_send_alert(
                    AlertType.DIGEST, alerts_sent_today=0, check_time=now
                ):
                    continue

                notification_type = (
                    NotificationType.DIGEST_DAILY
                    if frequency == AlertFrequency.DAILY
                    else NotificationType.DIGEST_WEEKLY
                )
                attempt_key = (prefs.user_email, notification_type)
                minute_key = now.strftime("%Y-%m-%d %H:%M")
                if self._last_attempt_minute.get(attempt_key) == minute_key:
                    continue
                self._last_attempt_minute[attempt_key] = minute_key

                if self._was_notification_sent_today(prefs.user_email, notification_type, now):
                    continue

                digest_type = "daily" if frequency == AlertFrequency.DAILY else "weekly"
                data = self._build_digest_data(prefs, now, digest_type=digest_type)
                alert_key = f"digest_{digest_type}_{now.strftime('%Y-%m-%d')}_{prefs.user_email}"
                if alert_key in am._sent_alerts:
                    continue

                record = self._history.record_notification(
                    user_email=prefs.user_email,
                    notification_type=notification_type,
                    subject=f"{digest_type.title()} Digest",
                    metadata={"digest_type": digest_type},
                )
                record_id = record.id

                ok = am.send_digest(
                    prefs.user_email,
                    digest_type=digest_type,
                    data=data,
                    send_email=True,
                )
                if ok:
                    self._history.mark_sent(record.id)
                    sent_count += 1
                else:
                    self._history.mark_failed(
                        record.id, "Digest send returned False", add_to_retry_queue=True
                    )
            except Exception as e:
                if record_id:
                    try:
                        self._history.mark_failed(record_id, str(e), add_to_retry_queue=True)
                    except Exception:
                        pass
                logger.warning(
                    "Digest send failed for %s: %s",
                    getattr(prefs, "user_email", "unknown"),
                    e,
                )
        return sent_count

    def _is_time_match(
        self, prefs: NotificationPreferences, now: datetime, frequency: AlertFrequency
    ) -> bool:
        try:
            target_time = datetime.strptime(prefs.daily_digest_time, "%H:%M").time()
        except Exception:
            return False

        if now.time().strftime("%H:%M") != target_time.strftime("%H:%M"):
            return False

        if frequency == AlertFrequency.WEEKLY:
            current_day = now.strftime("%A").lower()
            return current_day == prefs.weekly_digest_day.value

        return True

    def _was_notification_sent_today(
        self, user_email: str, notification_type: NotificationType, now: datetime
    ) -> bool:
        records = self._history.get_user_notifications(
            user_email, notification_type=notification_type
        )
        sent_statuses = {
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
            NotificationStatus.OPENED,
            NotificationStatus.CLICKED,
        }
        for r in records:
            if r.created_at.date() == now.date() and r.status in sent_statuses:
                return True
        return False

    def _build_digest_data(
        self, prefs: NotificationPreferences, now: datetime, *, digest_type: str
    ) -> Dict[str, Any]:
        current = load_collection()
        previous = load_previous_collection()
        if current is None:
            return {
                "new_properties": 0,
                "price_drops": 0,
                "avg_price": 0,
                "total_properties": 0,
                "average_price": 0,
                "trending_cities": [],
                "saved_searches": [],
                "top_picks": [],
                "price_drop_properties": [],
                "expert": None,
            }

        total_properties = current.total_count or len(current.properties)
        prices = [p.price for p in current.properties if p.price is not None]
        avg_price = sum(prices) / len(prices) if prices else 0

        city_counts: Dict[str, int] = {}
        for p in current.properties:
            city = (p.city or "").strip()
            if not city:
                continue
            city_counts[city] = city_counts.get(city, 0) + 1
        trending_cities = [
            c for c, _ in sorted(city_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
        ]

        am = AlertManager(email_service=self._email_service, storage_path=self._storage_path_alerts)

        new_props = []
        if previous is not None:
            prev_keys = {am._get_property_key(p) for p in previous.properties}
            for p in current.properties:
                if am._get_property_key(p) not in prev_keys:
                    new_props.append(p)

        price_drop_entries: List[Dict[str, Any]] = []
        price_drop_total = 0
        if previous is not None:
            drops = am.check_price_drops(
                current, previous, threshold_percent=prefs.price_drop_threshold
            )
            price_drop_total = len(drops)
            drops_sorted = sorted(drops, key=lambda d: d.get("percent_drop", 0), reverse=True)
            for d in drops_sorted[:5]:
                prop = d.get("property")
                if prop is None:
                    continue
                price_drop_entries.append(
                    {
                        "property": self._summarize_property(prop),
                        "old_price": d.get("old_price"),
                        "new_price": d.get("new_price"),
                        "percent_drop": d.get("percent_drop"),
                        "savings": d.get("savings"),
                    }
                )

        saved_search_summaries: List[Dict[str, Any]] = []
        searches = self._search_manager.get_all_searches()
        for s in searches:
            new_matches = 0
            for p in new_props:
                if s.matches(p.model_dump()):
                    new_matches += 1
            saved_search_summaries.append({"id": s.id, "name": s.name, "new_matches": new_matches})

        top_pick_candidates = new_props if new_props else list(current.properties)

        def top_pick_key(p) -> tuple[int, float]:
            if p.price_per_sqm is not None:
                return (0, float(p.price_per_sqm))
            if p.price is not None:
                return (1, float(p.price))
            return (2, float("inf"))

        top_picks = [
            self._summarize_property(p) for p in sorted(top_pick_candidates, key=top_pick_key)[:5]
        ]

        expert: Optional[Dict[str, Any]] = None
        if digest_type == "weekly":
            try:
                insights = MarketInsights(current)
                city_idx = insights.get_city_price_indices(None)
                yoy_latest = insights.get_cities_yoy(None)
                yoy_latest = (
                    yoy_latest.dropna(subset=["yoy_pct"])
                    if "yoy_pct" in yoy_latest.columns
                    else yoy_latest
                )
                top_up = (
                    yoy_latest.sort_values("yoy_pct", ascending=False)
                    .head(5)
                    .to_dict(orient="records")
                )
                top_down = (
                    yoy_latest.sort_values("yoy_pct", ascending=True)
                    .head(5)
                    .to_dict(orient="records")
                )
                expert = {
                    "city_indices": city_idx.head(10).to_dict(orient="records"),
                    "yoy_top_up": top_up,
                    "yoy_top_down": top_down,
                }
            except Exception:
                expert = None

        return {
            "new_properties": len(new_props),
            "price_drops": price_drop_total,
            "avg_price": avg_price,
            "total_properties": total_properties,
            "average_price": avg_price,
            "trending_cities": trending_cities,
            "saved_searches": saved_search_summaries,
            "top_picks": top_picks,
            "price_drop_properties": price_drop_entries,
            "expert": expert,
            "generated_at": now.isoformat(),
        }

    def _summarize_property(self, p: Any) -> Dict[str, Any]:
        return {
            "id": getattr(p, "id", None),
            "title": getattr(p, "title", None),
            "city": getattr(p, "city", None),
            "district": getattr(p, "district", None),
            "property_type": getattr(p, "property_type", None),
            "listing_type": getattr(p, "listing_type", None),
            "price": getattr(p, "price", None),
            "currency": getattr(p, "currency", None),
            "rooms": getattr(p, "rooms", None),
            "bathrooms": getattr(p, "bathrooms", None),
            "area_sqm": getattr(p, "area_sqm", None),
            "price_per_sqm": getattr(p, "price_per_sqm", None),
            "has_parking": getattr(p, "has_parking", False),
            "has_elevator": getattr(p, "has_elevator", False),
            "has_balcony": getattr(p, "has_balcony", False),
            "is_furnished": getattr(p, "is_furnished", False),
            "source_url": getattr(p, "source_url", None),
        }
