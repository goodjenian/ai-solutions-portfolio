import time

from notifications.email_service import EmailConfig, EmailProvider, EmailService
from notifications.uptime_monitor import UptimeMonitor, UptimeMonitorConfig


class FakeEmailService(EmailService):
    def __init__(self):
        cfg = EmailConfig(
            provider=EmailProvider.CUSTOM,
            smtp_server="localhost",
            smtp_port=1025,
            username="u",
            password="p",
            from_email="noreply@example.com",
        )
        super().__init__(cfg)
        self.sent = 0

    def send_email(self, *args, **kwargs):
        self.sent += 1
        return True


def test_uptime_monitor_sends_alert_on_consecutive_failures():
    # Checker fails three times then succeeds
    outcomes = [False, False, False, True]

    def checker():
        return outcomes.pop(0) if outcomes else True

    email = FakeEmailService()
    cfg = UptimeMonitorConfig(
        interval_seconds=0.01,
        fail_threshold=3,
        alert_cooldown_seconds=0.1,
        to_email="ops@example.com",
    )
    mon = UptimeMonitor(checker=checker, email_service=email, config=cfg)

    # Drive ticks synchronously
    mon.tick()
    mon.tick()
    mon.tick()  # should trigger alert
    assert email.sent == 1
    mon.tick()  # recover
    assert mon._consecutive_failures == 0


def test_uptime_monitor_cooldown_prevents_spam():
    # Always failing checker
    def checker():
        return False

    email = FakeEmailService()
    cfg = UptimeMonitorConfig(
        interval_seconds=0.01,
        fail_threshold=1,
        alert_cooldown_seconds=0.2,
        to_email="ops@example.com",
    )
    mon = UptimeMonitor(checker=checker, email_service=email, config=cfg)

    mon.tick()  # first alert
    assert email.sent == 1
    # Within cooldown, no additional alerts
    mon.tick()
    mon.tick()
    assert email.sent == 1
    # After cooldown, allow another alert
    time.sleep(0.21)
    mon.tick()
    assert email.sent == 2
