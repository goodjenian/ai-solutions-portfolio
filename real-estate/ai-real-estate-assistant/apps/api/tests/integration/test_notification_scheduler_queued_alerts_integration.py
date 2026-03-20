from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from data.schemas import Property, PropertyCollection, PropertyType
from notifications import (
    AlertFrequency,
    EmailService,
    NotificationHistory,
    NotificationPreferencesManager,
)
from notifications.alert_manager import AlertType
from notifications.notification_history import NotificationStatus, NotificationType
from notifications.scheduler import NotificationScheduler
from utils.saved_searches import SavedSearch, SavedSearchManager


@pytest.fixture
def scheduler_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from utils import property_cache

    cache_dir = tmp_path / "app_cache"
    monkeypatch.setattr(property_cache, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(property_cache, "CACHE_FILE", cache_dir / "properties.json")
    monkeypatch.setattr(property_cache, "PREV_CACHE_FILE", cache_dir / "properties_prev.json")

    prefs_manager = NotificationPreferencesManager(storage_path=str(tmp_path / "prefs"))
    history = NotificationHistory(storage_path=str(tmp_path / "history"))
    search_manager = SavedSearchManager(storage_path=str(tmp_path / "user_data"))

    email_service = Mock(spec=EmailService)
    email_service.send_email = Mock(return_value=True)

    scheduler = NotificationScheduler(
        email_service=email_service,
        prefs_manager=prefs_manager,
        history=history,
        search_manager=search_manager,
        poll_interval_seconds=1,
        storage_path_alerts=str(tmp_path / "alerts"),
        vector_store=None,
    )

    return {
        "property_cache": property_cache,
        "prefs_manager": prefs_manager,
        "history": history,
        "search_manager": search_manager,
        "email_service": email_service,
        "scheduler": scheduler,
    }


def test_queued_price_drop_alert_sends_after_quiet_hours(scheduler_context):
    property_cache = scheduler_context["property_cache"]
    prefs_manager = scheduler_context["prefs_manager"]
    history = scheduler_context["history"]
    search_manager = scheduler_context["search_manager"]
    email_service = scheduler_context["email_service"]
    scheduler = scheduler_context["scheduler"]

    user_email = "user@example.com"
    prefs_manager.update_preferences(
        user_email,
        alert_frequency=AlertFrequency.INSTANT,
        enabled_alerts={AlertType.PRICE_DROP},
        quiet_hours_start="22:00",
        quiet_hours_end="08:00",
        enabled=True,
    )

    search_manager.save_search(SavedSearch(id="s1", name="Krakow", city="Krakow"))

    previous = PropertyCollection(
        properties=[
            Property(
                id="p1",
                city="Krakow",
                price=1000,
                rooms=2,
                bathrooms=1,
                area_sqm=50,
                property_type=PropertyType.APARTMENT,
            )
        ],
        total_count=1,
    )
    property_cache.save_collection(previous)

    current = PropertyCollection(
        properties=[
            Property(
                id="p1",
                city="Krakow",
                price=900,
                rooms=2,
                bathrooms=1,
                area_sqm=50,
                property_type=PropertyType.APARTMENT,
            )
        ],
        total_count=1,
    )
    property_cache.save_collection(current)

    quiet_time = datetime(2025, 1, 1, 23, 0, 0)
    result_quiet = scheduler.run_pending(now=quiet_time)
    assert result_quiet["stats"]["queued_alerts"] == 1
    assert result_quiet["stats"]["queued_alerts_sent"] == 0

    property_cache.save_collection(current)

    email_service.send_email.reset_mock()
    send_time = datetime(2025, 1, 2, 9, 0, 0)
    result_send = scheduler.run_pending(now=send_time)
    assert result_send["stats"]["queued_alerts_sent"] == 1

    email_service.send_email.assert_called()

    records = history.get_user_notifications(
        user_email, notification_type=NotificationType.PRICE_DROP
    )
    assert len(records) == 1
    assert records[0].status == NotificationStatus.SENT


def test_queued_new_property_alert_sends_after_quiet_hours(scheduler_context):
    property_cache = scheduler_context["property_cache"]
    prefs_manager = scheduler_context["prefs_manager"]
    history = scheduler_context["history"]
    search_manager = scheduler_context["search_manager"]
    email_service = scheduler_context["email_service"]
    scheduler = scheduler_context["scheduler"]

    user_email = "user@example.com"
    prefs_manager.update_preferences(
        user_email,
        alert_frequency=AlertFrequency.INSTANT,
        enabled_alerts={AlertType.NEW_PROPERTY},
        quiet_hours_start="22:00",
        quiet_hours_end="08:00",
        enabled=True,
    )

    search_manager.save_search(SavedSearch(id="s1", name="Krakow", city="Krakow"))

    previous = PropertyCollection(properties=[], total_count=0)
    property_cache.save_collection(previous)

    current = PropertyCollection(
        properties=[
            Property(
                id="p1",
                city="Krakow",
                price=900,
                rooms=2,
                bathrooms=1,
                area_sqm=50,
                property_type=PropertyType.APARTMENT,
            )
        ],
        total_count=1,
    )
    property_cache.save_collection(current)

    quiet_time = datetime(2025, 1, 1, 23, 0, 0)
    result_quiet = scheduler.run_pending(now=quiet_time)
    assert result_quiet["stats"]["queued_alerts"] == 1
    assert result_quiet["stats"]["queued_alerts_sent"] == 0

    property_cache.save_collection(current)

    email_service.send_email.reset_mock()
    send_time = datetime(2025, 1, 2, 9, 0, 0)
    result_send = scheduler.run_pending(now=send_time)
    assert result_send["stats"]["queued_alerts_sent"] == 1

    email_service.send_email.assert_called()

    records = history.get_user_notifications(
        user_email, notification_type=NotificationType.NEW_PROPERTY
    )
    assert len(records) == 1
    assert records[0].status == NotificationStatus.SENT


def test_daily_digest_sends_and_records_history(scheduler_context):
    property_cache = scheduler_context["property_cache"]
    prefs_manager = scheduler_context["prefs_manager"]
    history = scheduler_context["history"]
    email_service = scheduler_context["email_service"]
    scheduler = scheduler_context["scheduler"]

    user_email = "user@example.com"
    prefs_manager.update_preferences(
        user_email,
        alert_frequency=AlertFrequency.DAILY,
        enabled_alerts={AlertType.DIGEST},
        daily_digest_time="09:00",
        enabled=True,
    )

    property_cache.save_collection(PropertyCollection(properties=[], total_count=0))

    email_service.send_email.reset_mock()
    send_time = datetime(2025, 1, 1, 9, 0, 0)
    result = scheduler.run_pending(now=send_time)
    assert result["stats"]["digests_daily"] == 1
    email_service.send_email.assert_called()

    records = history.get_user_notifications(
        user_email, notification_type=NotificationType.DIGEST_DAILY
    )
    assert len(records) == 1
    assert records[0].status == NotificationStatus.SENT
