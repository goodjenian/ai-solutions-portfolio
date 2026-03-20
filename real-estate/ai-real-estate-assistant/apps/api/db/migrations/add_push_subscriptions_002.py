"""
Migration: Add push_subscriptions table for Task #63

This migration creates the push_subscriptions table for storing
web push notification subscriptions for authenticated users.

Run with: python -m db.migrations.add_push_subscriptions_002
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db_context

logger = logging.getLogger(__name__)

MIGRATION_ID = "002_add_push_subscriptions"
MIGRATION_NAME = "Add push_subscriptions table"


async def up(session: AsyncSession) -> None:
    """Apply the migration."""
    logger.info(f"Running migration {MIGRATION_ID}: {MIGRATION_NAME}")

    await session.execute(
        text("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            endpoint VARCHAR(500) NOT NULL UNIQUE,
            p256dh VARCHAR(255) NOT NULL,
            auth VARCHAR(255) NOT NULL,
            user_agent VARCHAR(500),
            device_name VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_used_at TIMESTAMP WITH TIME ZONE
        )
        """)
    )

    # Create indexes
    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_push_user_active
        ON push_subscriptions(user_id, is_active)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_push_subscriptions_user_id
        ON push_subscriptions(user_id)
        """)
    )

    logger.info(f"Migration {MIGRATION_ID} completed successfully")


async def down(session: AsyncSession) -> None:
    """Rollback the migration."""
    logger.info(f"Rolling back migration {MIGRATION_ID}: {MIGRATION_NAME}")

    await session.execute(text("DROP INDEX IF EXISTS ix_push_subscriptions_user_id"))
    await session.execute(text("DROP INDEX IF EXISTS ix_push_user_active"))
    await session.execute(text("DROP TABLE IF EXISTS push_subscriptions"))

    logger.info(f"Migration {MIGRATION_ID} rolled back successfully")


async def run_migration() -> None:
    """Run the migration standalone."""
    async with get_db_context() as session:
        await up(session)
        logger.info("Migration completed. Run with down=True to rollback.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migration())
