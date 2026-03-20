from unittest.mock import patch

from data.schemas import Property, PropertyCollection, PropertyType
from notifications.alert_manager import Alert, AlertManager, AlertType
from notifications.email_service import EmailConfig, EmailProvider, EmailService
from utils.saved_searches import SavedSearch


def make_prop(pid, city, price, rooms, area=50):
    return Property(
        id=pid,
        city=city,
        price=price,
        rooms=rooms,
        bathrooms=1,
        area_sqm=area,
        property_type=PropertyType.APARTMENT,
        has_parking=True,
        is_furnished=True,
    )


def make_email_service():
    return EmailService(
        EmailConfig(
            provider=EmailProvider.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="u@example.com",
            password="pw",
            from_email="u@example.com",
        )
    )


def test_check_price_drops_and_send(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    prev = PropertyCollection(properties=[make_prop("p1", "Krakow", 1000, 2)], total_count=1)
    curr = PropertyCollection(properties=[make_prop("p1", "Krakow", 900, 2)], total_count=1)
    drops = am.check_price_drops(curr, prev, threshold_percent=5.0)
    assert len(drops) == 1 and drops[0]["savings"] == 100

    with patch.object(EmailService, "send_email", return_value=True):
        ok = am.send_price_drop_alert("user@example.com", drops[0], send_email=True)
        assert ok is True
        stats = am.get_alert_statistics()
        assert stats["total_sent"] >= 1

    # Duplicate should not send again
    with patch.object(EmailService, "send_email", return_value=True):
        ok2 = am.send_price_drop_alert("user@example.com", drops[0], send_email=True)
        assert ok2 is False


def test_check_new_property_matches_and_send(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    props = PropertyCollection(
        properties=[
            make_prop("p1", "Krakow", 900, 2),
            make_prop("p2", "Krakow", 1200, 3),
        ],
        total_count=2,
    )

    ss = SavedSearch(id="s1", name="Krakow Budget", city="Krakow", max_price=1000)
    matches = am.check_new_property_matches(props, [ss])
    assert "s1" in matches and len(matches["s1"]) == 1

    with patch.object(EmailService, "send_email", return_value=True):
        ok = am.send_new_property_alerts(
            "user@example.com", "s1", ss.name, matches["s1"], send_email=True
        )
        assert ok is True


def test_get_property_key_stable():
    svc = make_email_service()
    am = AlertManager(svc)
    p = make_prop(None, "Krakow", 900, 2, area=60)
    k1 = am._get_property_key(p)
    p2 = make_prop(None, "Krakow", 850, 2, area=60)
    k2 = am._get_property_key(p2)
    assert k1 == k2


def test_queue_price_drop_alert_serializes_property_and_processes(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    prop = make_prop("p1", "Krakow", 900, 2)
    drop = {
        "property": prop,
        "old_price": 1000,
        "new_price": 900,
        "percent_drop": 10.0,
        "savings": 100,
    }
    am.queue_alert(
        Alert(
            alert_type=AlertType.PRICE_DROP,
            user_email="user@example.com",
            data=drop,
            property_id="p1",
        )
    )

    pending = am.list_pending_alerts()
    assert len(pending) == 1
    assert isinstance(pending[0].data["property"], dict)

    with patch.object(EmailService, "send_email", return_value=True):
        sent_count, sent_alerts = am.process_pending_alerts_with_result()
        assert sent_count == 1
        assert len(sent_alerts) == 1
        assert am.list_pending_alerts() == []


def test_process_pending_alerts_respects_predicate(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    prop = make_prop("p1", "Krakow", 900, 2)
    drop = {
        "property": prop,
        "old_price": 1000,
        "new_price": 900,
        "percent_drop": 10.0,
        "savings": 100,
    }
    am.queue_alert(
        Alert(
            alert_type=AlertType.PRICE_DROP,
            user_email="user@example.com",
            data=drop,
            property_id="p1",
        )
    )

    with patch.object(EmailService, "send_email", return_value=True) as send_mock:
        sent_count, sent_alerts = am.process_pending_alerts_with_result(
            should_send=lambda _a: False
        )
        assert sent_count == 0
        assert sent_alerts == []
        assert len(am.list_pending_alerts()) == 1
        send_mock.assert_not_called()


def test_process_pending_alerts_keeps_transient_failures(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    prop = make_prop("p1", "Krakow", 900, 2)
    drop = {
        "property": prop,
        "old_price": 1000,
        "new_price": 900,
        "percent_drop": 10.0,
        "savings": 100,
    }
    am.queue_alert(
        Alert(
            alert_type=AlertType.PRICE_DROP,
            user_email="user@example.com",
            data=drop,
            property_id="p1",
        )
    )

    with patch.object(EmailService, "send_email", side_effect=Exception("smtp down")):
        sent_count, sent_alerts = am.process_pending_alerts_with_result()
        assert sent_count == 0
        assert sent_alerts == []
        assert len(am.list_pending_alerts()) == 1


def test_process_pending_alerts_drops_duplicates(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    prop = make_prop("p1", "Krakow", 900, 2)
    drop = {
        "property": prop,
        "old_price": 1000,
        "new_price": 900,
        "percent_drop": 10.0,
        "savings": 100,
    }

    with patch.object(EmailService, "send_email", return_value=True) as send_mock:
        am.queue_alert(
            Alert(
                alert_type=AlertType.PRICE_DROP,
                user_email="user@example.com",
                data=drop,
                property_id="p1",
            )
        )
        sent_count, _sent_alerts = am.process_pending_alerts_with_result()
        assert sent_count == 1

        send_mock.reset_mock()
        am.queue_alert(
            Alert(
                alert_type=AlertType.PRICE_DROP,
                user_email="user@example.com",
                data=drop,
                property_id="p1",
            )
        )
        sent_count2, sent_alerts2 = am.process_pending_alerts_with_result()
        assert sent_count2 == 0
        assert sent_alerts2 == []
        assert am.list_pending_alerts() == []
        send_mock.assert_not_called()


def test_send_price_drop_alert_accepts_property_dict(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    prop = make_prop("p1", "Krakow", 900, 2)
    prop_dict = prop.model_dump(mode="json") if hasattr(prop, "model_dump") else prop.dict()
    drop = {
        "property": prop_dict,
        "old_price": 1000,
        "new_price": 900,
        "percent_drop": 10.0,
        "savings": 100,
    }

    with patch.object(EmailService, "send_email", return_value=True):
        ok = am.send_price_drop_alert("user@example.com", drop, send_email=True)
        assert ok is True
        ok2 = am.send_price_drop_alert("user@example.com", drop, send_email=True)
        assert ok2 is False


def test_queue_new_property_alert_roundtrip_and_send(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    prop = make_prop("p1", "Krakow", 900, 2)
    prop_dict = prop.model_dump(mode="json") if hasattr(prop, "model_dump") else prop.dict()
    alert = Alert(
        alert_type=AlertType.NEW_PROPERTY,
        user_email="user@example.com",
        data={"search_id": "s1", "search_name": "Krakow", "properties": [prop_dict]},
    )

    with patch.object(EmailService, "send_email", return_value=True):
        am.queue_alert(alert)
        assert len(am.list_pending_alerts()) == 1
        sent_count, sent_alerts = am.process_pending_alerts_with_result()
        assert sent_count == 1
        assert len(sent_alerts) == 1
        assert am.list_pending_alerts() == []


def test_queue_price_drop_alert_serialization_uses_model_dump_when_available(monkeypatch, tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    def _fake_model_dump(self, **_kwargs):
        return {
            "id": self.id,
            "city": self.city,
            "price": self.price,
            "rooms": self.rooms,
            "bathrooms": self.bathrooms,
        }

    monkeypatch.setattr(Property, "model_dump", _fake_model_dump, raising=False)

    prop = make_prop("p1", "Krakow", 900, 2)
    drop = {
        "property": prop,
        "old_price": 1000,
        "new_price": 900,
        "percent_drop": 10.0,
        "savings": 100,
    }
    am.queue_alert(
        Alert(
            alert_type=AlertType.PRICE_DROP,
            user_email="user@example.com",
            data=drop,
            property_id="p1",
        )
    )
    assert len(am.list_pending_alerts()) == 1


def test_queue_price_drop_alert_serialization_falls_back_to_json(monkeypatch, tmp_path):
    import json

    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    def _boom_model_dump(self, **_kwargs):
        raise RuntimeError("boom")

    def _fake_json(self, **_kwargs):
        return json.dumps(
            {
                "id": self.id,
                "city": self.city,
                "price": self.price,
                "rooms": self.rooms,
                "bathrooms": self.bathrooms,
            }
        )

    monkeypatch.setattr(Property, "model_dump", _boom_model_dump, raising=False)
    monkeypatch.setattr(Property, "json", _fake_json, raising=False)

    prop = make_prop("p1", "Krakow", 900, 2)
    drop = {
        "property": prop,
        "old_price": 1000,
        "new_price": 900,
        "percent_drop": 10.0,
        "savings": 100,
    }
    am.queue_alert(
        Alert(
            alert_type=AlertType.PRICE_DROP,
            user_email="user@example.com",
            data=drop,
            property_id="p1",
        )
    )
    assert len(am.list_pending_alerts()) == 1


def test_queue_price_drop_alert_serialization_falls_back_to_dict(monkeypatch, tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    def _boom_model_dump(self, **_kwargs):
        raise RuntimeError("boom")

    def _boom_json(self, **_kwargs):
        raise RuntimeError("boom")

    def _fake_dict(self, **_kwargs):
        return {
            "id": self.id,
            "city": self.city,
            "price": self.price,
            "rooms": self.rooms,
            "bathrooms": self.bathrooms,
        }

    monkeypatch.setattr(Property, "model_dump", _boom_model_dump, raising=False)
    monkeypatch.setattr(Property, "json", _boom_json, raising=False)
    monkeypatch.setattr(Property, "dict", _fake_dict, raising=False)

    prop = make_prop("p1", "Krakow", 900, 2)
    drop = {
        "property": prop,
        "old_price": 1000,
        "new_price": 900,
        "percent_drop": 10.0,
        "savings": 100,
    }
    am.queue_alert(
        Alert(
            alert_type=AlertType.PRICE_DROP,
            user_email="user@example.com",
            data=drop,
            property_id="p1",
        )
    )
    assert len(am.list_pending_alerts()) == 1


def test_process_pending_digest_alert_roundtrip_and_dedup(tmp_path):
    svc = make_email_service()
    am = AlertManager(svc, storage_path=str(tmp_path))

    digest_alert = Alert(
        alert_type=AlertType.DIGEST,
        user_email="user@example.com",
        data={
            "digest_type": "daily",
            "content": {
                "new_properties": 0,
                "price_drops": 0,
                "trending_cities": [],
                "saved_searches": [],
                "top_picks": [],
                "expert": None,
            },
        },
    )

    with patch.object(EmailService, "send_email", return_value=True) as send_mock:
        am.queue_alert(digest_alert)
        sent_count, sent_alerts = am.process_pending_alerts_with_result()
        assert sent_count == 1
        assert len(sent_alerts) == 1
        assert am.list_pending_alerts() == []
        send_mock.assert_called()

        send_mock.reset_mock()
        am.queue_alert(digest_alert)
        sent_count2, sent_alerts2 = am.process_pending_alerts_with_result()
        assert sent_count2 == 0
        assert sent_alerts2 == []
        assert am.list_pending_alerts() == []
        send_mock.assert_not_called()
