import json
from datetime import datetime

from notifications.alert_storage_stats import load_alert_storage_summary


def test_load_alert_storage_summary_returns_zeros_when_files_missing(tmp_path):
    summary = load_alert_storage_summary(str(tmp_path))
    assert summary.sent_total == 0
    assert summary.pending_total == 0
    assert summary.pending_by_type == {}
    assert summary.pending_oldest_created_at is None
    assert summary.pending_newest_created_at is None


def test_load_alert_storage_summary_counts_pending_and_sent_and_tracks_oldest_newest(tmp_path):
    (tmp_path / "sent_alerts.json").write_text(
        json.dumps({"alerts": ["a", "b"], "last_updated": "2026-01-24T10:00:00"}), encoding="utf-8"
    )
    (tmp_path / "pending_alerts.json").write_text(
        json.dumps(
            {
                "alerts": [
                    {"alert_type": "price_drop", "created_at": "2026-01-24T12:00:00"},
                    {"alert_type": "new_property", "created_at": "2026-01-24T10:00:00"},
                    {"alert_type": "new_property", "created_at": "not-a-date"},
                    "not-a-dict",
                ],
                "last_updated": "2026-01-24T12:01:00",
            }
        ),
        encoding="utf-8",
    )

    summary = load_alert_storage_summary(str(tmp_path))
    assert summary.sent_total == 2
    assert summary.pending_total == 4
    assert summary.pending_by_type["price_drop"] == 1
    assert summary.pending_by_type["new_property"] == 2

    assert summary.pending_oldest_created_at == datetime(2026, 1, 24, 10, 0, 0)
    assert summary.pending_newest_created_at == datetime(2026, 1, 24, 12, 0, 0)


def test_load_alert_storage_summary_handles_invalid_json(tmp_path):
    (tmp_path / "sent_alerts.json").write_text("{", encoding="utf-8")
    (tmp_path / "pending_alerts.json").write_text("{", encoding="utf-8")
    summary = load_alert_storage_summary(str(tmp_path))
    assert summary.sent_total == 0
    assert summary.pending_total == 0
