from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from data.schemas import Property, PropertyCollection, PropertyType
from notifications import (
    AlertFrequency,
    DigestDay,
    EmailService,
    NotificationHistory,
    NotificationPreferencesManager,
)
from notifications.notification_preferences import AlertType as PrefAlertType
from notifications.notification_preferences import DigestScheduler
from utils.saved_searches import SavedSearchManager


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

    scheduler = DigestScheduler(
        email_service=email_service,
        prefs_manager=prefs_manager,
        history=history,
        search_manager=search_manager,
        poll_interval_seconds=1,
        storage_path_alerts=str(tmp_path / "alerts"),
    )

    return {
        "property_cache": property_cache,
        "prefs_manager": prefs_manager,
        "history": history,
        "search_manager": search_manager,
        "email_service": email_service,
        "scheduler": scheduler,
    }


def test_daily_digest_includes_top_picks(scheduler_context):
    property_cache = scheduler_context["property_cache"]
    prefs_manager = scheduler_context["prefs_manager"]
    email_service = scheduler_context["email_service"]
    scheduler = scheduler_context["scheduler"]

    user_email = "daily@example.com"
    prefs_manager.update_preferences(
        user_email,
        alert_frequency=AlertFrequency.DAILY,
        daily_digest_time="09:00",
        enabled_alerts={PrefAlertType.DIGEST},
    )

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
            previous.properties[0],
            Property(
                id="p2",
                city="Krakow",
                price=900,
                rooms=2,
                bathrooms=1,
                area_sqm=55,
                property_type=PropertyType.APARTMENT,
                source_url="https://example.com/p2",
            ),
        ],
        total_count=2,
    )
    property_cache.save_collection(current)

    now = datetime(2025, 1, 1, 9, 0)
    result = scheduler.run_pending(now=now)
    assert result["sent"]["daily"] == 1

    sent_body = email_service.send_email.call_args.kwargs["body"]
    assert "Top Picks" in sent_body
    assert "https://example.com/p2" in sent_body


def test_weekly_digest_includes_expert_digest_section(scheduler_context):
    property_cache = scheduler_context["property_cache"]
    prefs_manager = scheduler_context["prefs_manager"]
    email_service = scheduler_context["email_service"]
    scheduler = scheduler_context["scheduler"]

    user_email = "weekly@example.com"
    prefs_manager.update_preferences(
        user_email,
        alert_frequency=AlertFrequency.WEEKLY,
        daily_digest_time="09:00",
        weekly_digest_day=DigestDay.WEDNESDAY,
        enabled_alerts={PrefAlertType.DIGEST},
    )

    current = PropertyCollection(
        properties=[
            Property(
                id="w1",
                city="Warsaw",
                price=1200,
                rooms=3,
                bathrooms=2,
                area_sqm=75,
                property_type=PropertyType.APARTMENT,
            )
        ],
        total_count=1,
    )
    property_cache.save_collection(current)
    property_cache.save_collection(current)

    email_service.send_email.reset_mock()
    wednesday = datetime(2025, 1, 1, 9, 0)
    result = scheduler.run_pending(now=wednesday)
    assert result["sent"]["weekly"] == 1

    sent_body = email_service.send_email.call_args.kwargs["body"]
    assert "Expert Digest" in sent_body
