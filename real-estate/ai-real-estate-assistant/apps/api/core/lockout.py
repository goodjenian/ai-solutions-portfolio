"""Account lockout management for authentication security (Task #47).

This module provides account lockout functionality to prevent brute force attacks:
- Track failed login attempts per user
- Lock accounts after too many failed attempts
- Automatic unlock after lockout duration expires
- Admin unlock capability
"""

from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from db.models import User


class AccountLockoutService:
    """Manages account lockout after failed login attempts."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the lockout service.

        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
        settings = get_settings()
        self._max_attempts = settings.auth_lockout_max_attempts
        self._lockout_duration_minutes = settings.auth_lockout_duration_minutes

    async def check_lockout(self, user: User) -> tuple[bool, Optional[int]]:
        """
        Check if an account is currently locked.

        Args:
            user: The user to check

        Returns:
            Tuple of (is_locked, locked_for_seconds)
            - is_locked: True if account is currently locked
            - locked_for_seconds: Seconds until unlock (None if not locked)
        """
        if user.locked_until is None:
            return False, None

        now = datetime.now(UTC)
        if now >= user.locked_until:
            # Lockout has expired, clear it
            await self._clear_lockout(user)
            return False, None

        # Calculate remaining time
        remaining = user.locked_until - now
        return True, int(remaining.total_seconds())

    async def record_failed_attempt(self, user: User) -> tuple[bool, Optional[int]]:
        """
        Record a failed login attempt and lock account if threshold reached.

        Args:
            user: The user with failed attempt

        Returns:
            Tuple of (is_locked, locked_for_seconds)
            - is_locked: True if account is now locked
            - locked_for_seconds: Seconds until unlock (None if not locked)
        """
        # Increment failed attempts
        user.failed_login_attempts += 1

        # Check if we should lock the account
        if user.failed_login_attempts >= self._max_attempts:
            locked_until = datetime.now(UTC) + timedelta(minutes=self._lockout_duration_minutes)
            user.locked_until = locked_until
            await self.session.commit()

            return True, self._lockout_duration_minutes * 60

        await self.session.commit()
        return False, None

    async def clear_failed_attempts(self, user: User) -> None:
        """
        Clear failed login attempts after successful login.

        This also clears any existing lockout.

        Args:
            user: The user to clear attempts for
        """
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.session.commit()

    async def unlock_account(self, user: User) -> None:
        """
        Admin function to manually unlock an account.

        Clears both the lockout and failed attempts counter.

        Args:
            user: The user to unlock
        """
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.session.commit()

    async def _clear_lockout(self, user: User) -> None:
        """
        Clear an expired lockout.

        This preserves the failed attempts counter - it will be cleared
        on next successful login.

        Args:
            user: The user with expired lockout
        """
        user.locked_until = None
        await self.session.commit()

    async def get_lockout_status(self, user: User) -> dict:
        """
        Get detailed lockout status for a user.

        Args:
            user: The user to check

        Returns:
            Dict with lockout details:
            - is_locked: bool
            - failed_attempts: int
            - max_attempts: int
            - locked_until: Optional[datetime]
            - lockout_duration_minutes: int
        """
        is_locked, _ = await self.check_lockout(user)

        return {
            "is_locked": is_locked,
            "failed_attempts": user.failed_login_attempts,
            "max_attempts": self._max_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "lockout_duration_minutes": self._lockout_duration_minutes,
        }


def get_lockout_service(session: AsyncSession) -> AccountLockoutService:
    """
    Factory function to create a lockout service.

    Args:
        session: SQLAlchemy async session

    Returns:
        AccountLockoutService instance
    """
    return AccountLockoutService(session)
