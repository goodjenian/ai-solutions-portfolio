from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from notifications.email_service import EmailService


@dataclass
class UptimeMonitorConfig:
    interval_seconds: float = 60.0
    fail_threshold: int = 3
    alert_cooldown_seconds: float = 1800.0  # 30 minutes
    to_email: str = "ops@example.com"
    subject: str = "Uptime Alert: Service Down"


class UptimeMonitor:
    """
    Simple uptime monitor that calls a checker function periodically and sends
    an alert email if consecutive failures reach the threshold.
    """

    def __init__(
        self,
        checker: Callable[[], bool],
        email_service: EmailService,
        config: Optional[UptimeMonitorConfig] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.checker = checker
        self.email_service = email_service
        self.config = config or UptimeMonitorConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._consecutive_failures = 0
        self._last_alert_ts: float = 0.0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="UptimeMonitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.tick()
            except Exception as e:
                self.logger.error("uptime_monitor_tick_error: %s", e)
            finally:
                self._stop_event.wait(self.config.interval_seconds)

    def tick(self) -> None:
        ok = False
        try:
            ok = bool(self.checker())
        except Exception as e:
            self.logger.warning("uptime_monitor_checker_exception: %s", e)
            ok = False

        if ok:
            if self._consecutive_failures > 0:
                self.logger.info("uptime_monitor_recovered after=%s", self._consecutive_failures)
            self._consecutive_failures = 0
            return

        self._consecutive_failures += 1
        self.logger.info("uptime_monitor_failure_count=%s", self._consecutive_failures)

        if self._consecutive_failures >= self.config.fail_threshold:
            now = time.time()
            if now - self._last_alert_ts < self.config.alert_cooldown_seconds:
                return
            # Send alert
            body = (
                "<html><body>"
                "<h3>Service Uptime Alert</h3>"
                f"<p>Checker has failed {self._consecutive_failures} times in a row.</p>"
                "<p>Please investigate the API availability.</p>"
                "</body></html>"
            )
            try:
                self.email_service.send_email(
                    to_email=self.config.to_email,
                    subject=self.config.subject,
                    body=body,
                    html=True,
                )
                self.logger.info("uptime_monitor_alert_sent to=%s", self.config.to_email)
                self._last_alert_ts = now
            except Exception as e:
                self.logger.error("uptime_monitor_alert_failed: %s", e)


def make_http_checker(url: str, timeout: float = 3.0) -> Callable[[], bool]:
    """
    Create a checker that performs a HTTP GET to the given URL and
    returns True when status_code == 200, False otherwise.
    """
    import requests

    def _check() -> bool:
        try:
            resp = requests.get(url, timeout=timeout)
            return int(getattr(resp, "status_code", 0)) == 200
        except Exception:
            return False

    return _check
