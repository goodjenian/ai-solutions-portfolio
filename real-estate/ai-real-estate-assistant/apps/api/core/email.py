"""Email service abstraction.

Provides a unified interface for sending emails with pluggable providers:
- ConsoleEmailProvider: Logs emails to console (development)
- SmtpEmailProvider: Sends via SMTP server (production)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message data."""

    to: str
    subject: str
    body: str
    html_body: Optional[str] = None
    from_address: Optional[str] = None


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    async def send(self, message: EmailMessage) -> bool:
        """Send an email message.

        Args:
            message: Email message to send

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass


class ConsoleEmailProvider(EmailProvider):
    """Email provider that logs emails to console.

    Useful for development and testing.
    """

    @property
    def name(self) -> str:
        return "console"

    async def send(self, message: EmailMessage) -> bool:
        """Log email to console."""
        logger.info(
            "email_sent",
            extra={
                "event": "email_sent",
                "provider": self.name,
                "to": message.to,
                "subject": message.subject,
                "body": message.body[:200] + "..." if len(message.body) > 200 else message.body,
            },
        )
        # Also print to stdout for visibility
        print(f"\n{'=' * 60}")
        print(f"EMAIL to: {message.to}")
        print(f"Subject: {message.subject}")
        print(f"{'=' * 60}")
        print(message.body)
        if message.html_body:
            print(f"\n--- HTML ---\n{message.html_body[:500]}...")
        print(f"{'=' * 60}\n")
        return True


class SmtpEmailProvider(EmailProvider):
    """Email provider that sends via SMTP."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_address: str,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.use_tls = use_tls

    @property
    def name(self) -> str:
        return "smtp"

    async def send(self, message: EmailMessage) -> bool:
        """Send email via SMTP."""
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        import aiosmtplib

        msg = MIMEMultipart("alternative")
        msg["Subject"] = message.subject
        msg["From"] = message.from_address or self.from_address
        msg["To"] = message.to

        # Add plain text body
        msg.attach(MIMEText(message.body, "plain"))

        # Add HTML body if provided
        if message.html_body:
            msg.attach(MIMEText(message.html_body, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=self.use_tls,
            )
            logger.info(
                "email_sent",
                extra={
                    "event": "email_sent",
                    "provider": self.name,
                    "to": message.to,
                    "subject": message.subject,
                },
            )
            return True
        except Exception as e:
            logger.error(
                "email_send_failed",
                extra={
                    "event": "email_send_failed",
                    "provider": self.name,
                    "to": message.to,
                    "error": str(e),
                },
            )
            return False


class EmailService:
    """Email service with provider abstraction."""

    def __init__(self, provider: EmailProvider, from_address: str):
        self.provider = provider
        self.from_address = from_address

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body

        Returns:
            True if sent successfully
        """
        message = EmailMessage(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            from_address=self.from_address,
        )
        return await self.provider.send(message)

    async def send_password_reset_email(
        self,
        to: str,
        reset_token: str,
        reset_url: str,
    ) -> bool:
        """Send password reset email."""
        subject = "Reset Your Password"
        body = f"""
You requested to reset your password.

Click the link below to reset your password:
{reset_url}?token={reset_token}

This link will expire in 1 hour.

If you did not request this, please ignore this email.
"""
        html_body = f"""
<html>
<body>
<p>You requested to reset your password.</p>
<p><a href="{reset_url}?token={reset_token}">Click here to reset your password</a></p>
<p>This link will expire in 1 hour.</p>
<p>If you did not request this, please ignore this email.</p>
</body>
</html>
"""
        return await self.send(to, subject, body, html_body)

    async def send_verification_email(
        self,
        to: str,
        verification_token: str,
        verification_url: str,
    ) -> bool:
        """Send email verification email."""
        subject = "Verify Your Email Address"
        body = f"""
Please verify your email address.

Click the link below to verify:
{verification_url}?token={verification_token}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.
"""
        html_body = f"""
<html>
<body>
<p>Please verify your email address.</p>
<p><a href="{verification_url}?token={verification_token}">Click here to verify your email</a></p>
<p>This link will expire in 24 hours.</p>
<p>If you did not create an account, please ignore this email.</p>
</body>
</html>
"""
        return await self.send(to, subject, body, html_body)


def create_email_service(
    provider: str = "console",
    from_address: str = "noreply@example.com",
    smtp_host: Optional[str] = None,
    smtp_port: int = 587,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    smtp_use_tls: bool = True,
) -> EmailService:
    """Create an email service with the specified provider.

    Args:
        provider: Provider type ("console" or "smtp")
        from_address: Default from address
        smtp_*: SMTP configuration (required if provider is "smtp")

    Returns:
        Configured EmailService instance
    """
    if provider == "smtp":
        if not smtp_host or not smtp_username or not smtp_password:
            logger.warning("SMTP configuration incomplete, falling back to console provider")
            email_provider: EmailProvider = ConsoleEmailProvider()
        else:
            email_provider = SmtpEmailProvider(
                host=smtp_host,
                port=smtp_port,
                username=smtp_username,
                password=smtp_password,
                from_address=from_address,
                use_tls=smtp_use_tls,
            )
    else:
        email_provider = ConsoleEmailProvider()

    return EmailService(provider=email_provider, from_address=from_address)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the global email service instance."""
    global _email_service
    if _email_service is None:
        from config.settings import get_settings

        settings = get_settings()
        _email_service = create_email_service(
            provider=getattr(settings, "email_provider", "console"),
            from_address=getattr(settings, "email_from_address", "noreply@example.com"),
            smtp_host=getattr(settings, "smtp_host", None),
            smtp_port=getattr(settings, "smtp_port", 587),
            smtp_username=getattr(settings, "smtp_username", None),
            smtp_password=getattr(settings, "smtp_password", None),
        )
    return _email_service


def init_email_service(
    provider: str,
    from_address: str,
    smtp_host: Optional[str] = None,
    smtp_port: int = 587,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
) -> EmailService:
    """Initialize the global email service."""
    global _email_service
    _email_service = create_email_service(
        provider=provider,
        from_address=from_address,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
    )
    return _email_service
