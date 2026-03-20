"""
Migration: Add market_anomalies table for Task #53

This migration creates the market_anomalies table for storing detected
market anomalies including price spikes, drops, and unusual patterns.

Run with: python -m db.migrations.001_add_market_anomalies
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db_context

logger = logging.getLogger(__name__)

MIGRATION_ID = "001_add_market_anomalies"
MIGRATION_NAME = "Add market_anomalies table"


async def up(session: AsyncSession) -> None:
    """Apply the migration."""
    logger.info(f"Running migration {MIGRATION_ID}: {MIGRATION_NAME}")

    await session.execute(
        text("""
        CREATE TABLE IF NOT EXISTS market_anomalies (
            id VARCHAR(36) PRIMARY KEY,
            anomaly_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            scope_type VARCHAR(20) NOT NULL,
            scope_id VARCHAR(255) NOT NULL,
            detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            algorithm VARCHAR(50) NOT NULL,
            threshold_used FLOAT NOT NULL,
            metric_name VARCHAR(50) NOT NULL,
            expected_value FLOAT NOT NULL,
            actual_value FLOAT NOT NULL,
            deviation_percent FLOAT NOT NULL,
            z_score FLOAT,
            alert_sent BOOLEAN DEFAULT FALSE,
            alert_sent_at TIMESTAMP WITH TIME ZONE,
            dismissed_by VARCHAR(36),
            dismissed_at TIMESTAMP WITH TIME ZONE,
            context JSON NOT NULL DEFAULT '{}'
        )
        """)
    )

    # Create indexes
    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_anomalies_scope_detected
        ON market_anomalies(scope_type, scope_id, detected_at)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_anomalies_severity
        ON market_anomalies(severity)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_anomalies_type
        ON market_anomalies(anomaly_type)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_anomalies_detected_at
        ON market_anomalies(detected_at DESC)
        """)
    )

    logger.info(f"Migration {MIGRATION_ID} completed successfully")


async def down(session: AsyncSession) -> None:
    """Rollback the migration."""
    logger.info(f"Rolling back migration {MIGRATION_ID}: {MIGRATION_NAME}")

    await session.execute(text("DROP TABLE IF EXISTS market_anomalies"))

    logger.info(f"Migration {MIGRATION_ID} rolled back successfully")


async def run_migration() -> None:
    """Run the migration standalone."""
    async with get_db_context() as session:
        await up(session)
        logger.info("Migration completed. Run with down=True to rollback.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migration())
