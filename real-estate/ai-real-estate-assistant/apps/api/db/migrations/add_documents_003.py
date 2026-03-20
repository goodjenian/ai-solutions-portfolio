"""
Migration: Add documents table for Task #43

This migration creates the documents table for storing
user property-related documents with OCR support.

Run with: python -m db.migrations.add_documents_003
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db_context

logger = logging.getLogger(__name__)

MIGRATION_ID = "003_add_documents"
MIGRATION_NAME = "Add documents table"


async def up(session: AsyncSession) -> None:
    """Apply the migration."""
    logger.info(f"Running migration {MIGRATION_ID}: {MIGRATION_NAME}")

    await session.execute(
        text("""
        CREATE TABLE IF NOT EXISTS documents (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            property_id VARCHAR(255),
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_size INTEGER NOT NULL,
            storage_path VARCHAR(500) NOT NULL,
            category VARCHAR(50),
            tags TEXT,
            description TEXT,
            extracted_text TEXT,
            ocr_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            expiry_date TIMESTAMP WITH TIME ZONE,
            expiry_notified BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
        """)
    )

    # Create indexes
    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_documents_user_id
        ON documents(user_id)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_documents_property_id
        ON documents(property_id)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_documents_category
        ON documents(category)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_documents_ocr_status
        ON documents(ocr_status)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_documents_expiry
        ON documents(expiry_date)
        """)
    )

    # Composite index for common query patterns
    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_documents_user_category
        ON documents(user_id, category)
        """)
    )

    await session.execute(
        text("""
        CREATE INDEX IF NOT EXISTS ix_documents_user_property
        ON documents(user_id, property_id)
        """)
    )

    logger.info(f"Migration {MIGRATION_ID} completed successfully")


async def down(session: AsyncSession) -> None:
    """Rollback the migration."""
    logger.info(f"Rolling back migration {MIGRATION_ID}: {MIGRATION_NAME}")

    await session.execute(text("DROP INDEX IF EXISTS ix_documents_user_property"))
    await session.execute(text("DROP INDEX IF EXISTS ix_documents_user_category"))
    await session.execute(text("DROP INDEX IF EXISTS ix_documents_expiry"))
    await session.execute(text("DROP INDEX IF EXISTS ix_documents_ocr_status"))
    await session.execute(text("DROP INDEX IF EXISTS ix_documents_category"))
    await session.execute(text("DROP INDEX IF EXISTS ix_documents_property_id"))
    await session.execute(text("DROP INDEX IF EXISTS ix_documents_user_id"))
    await session.execute(text("DROP TABLE IF EXISTS documents"))

    logger.info(f"Migration {MIGRATION_ID} rolled back successfully")


async def run_migration() -> None:
    """Run the migration standalone."""
    async with get_db_context() as session:
        await up(session)
        logger.info("Migration completed. Run with down=True to rollback.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migration())
