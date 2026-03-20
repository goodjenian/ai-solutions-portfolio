"""Repository pattern for database operations."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    AgentAssignment,
    AgentInquiry,
    AgentListing,
    AgentProfile,
    CollectionDB,
    DocumentDB,
    DocumentTemplateDB,
    EmailVerificationToken,
    FavoriteDB,
    Lead,
    LeadInteraction,
    LeadScore,
    MarketAnomaly,
    OAuthAccount,
    PasswordResetToken,
    PriceSnapshot,
    PushSubscription,
    RefreshToken,
    SavedSearchDB,
    SignatureRequestDB,
    SignedDocumentDB,
    User,
    ViewingAppointment,
)


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        hashed_password: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "user",
        is_verified: bool = False,
    ) -> User:
        """Create a new user."""
        user = User(
            id=str(uuid4()),
            email=email.lower().strip(),
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_verified=is_verified,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalar_one_or_none()

    async def update(self, user: User, **kwargs) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.session.flush()
        return user

    async def update_last_login(self, user: User) -> None:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.now(UTC)
        await self.session.flush()

    async def set_verified(self, user: User) -> None:
        """Mark user as verified."""
        user.is_verified = True
        await self.session.flush()

    async def set_password(self, user: User, hashed_password: str) -> None:
        """Set user's password."""
        user.hashed_password = hashed_password
        await self.session.flush()

    async def delete(self, user: User) -> None:
        """Delete a user."""
        await self.session.delete(user)

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        result = await self.session.execute(
            select(User.id).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none() is not None


class RefreshTokenRepository:
    """Repository for RefreshToken model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def create(
        self,
        user_id: str,
        token: str,
        expires_days: int = 7,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> RefreshToken:
        """Create a new refresh token."""
        token_hash = self._hash_token(token)
        refresh_token = RefreshToken(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=expires_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        return refresh_token

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token value."""
        token_hash = self._hash_token(token)
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> None:
        """Revoke a refresh token."""
        token.revoked_at = datetime.now(UTC)
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )

    async def cleanup_expired(self, user_id: Optional[str] = None) -> int:
        """Remove expired tokens."""
        query = select(RefreshToken).where(RefreshToken.expires_at < datetime.now(UTC))
        if user_id:
            query = query.where(RefreshToken.user_id == user_id)

        result = await self.session.execute(query)
        expired_tokens = result.scalars().all()

        count = 0
        for token in expired_tokens:
            await self.session.delete(token)
            count += 1

        return count


class OAuthAccountRepository:
    """Repository for OAuthAccount model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str] = None,
    ) -> OAuthAccount:
        """Create a new OAuth account link."""
        oauth_account = OAuthAccount(
            id=str(uuid4()),
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
        )
        self.session.add(oauth_account)
        await self.session.flush()
        return oauth_account

    async def get_by_provider(self, provider: str, provider_user_id: str) -> Optional[OAuthAccount]:
        """Get OAuth account by provider and provider user ID."""
        result = await self.session.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str) -> list[OAuthAccount]:
        """Get all OAuth accounts for a user."""
        result = await self.session.execute(
            select(OAuthAccount).where(OAuthAccount.user_id == user_id)
        )
        return list(result.scalars().all())

    async def delete(self, oauth_account: OAuthAccount) -> None:
        """Delete an OAuth account link."""
        await self.session.delete(oauth_account)


class PasswordResetTokenRepository:
    """Repository for PasswordResetToken model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def create(self, user_id: str, token: str, expires_hours: int = 1) -> PasswordResetToken:
        """Create a new password reset token."""
        token_hash = self._hash_token(token)
        reset_token = PasswordResetToken(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(hours=expires_hours),
        )
        self.session.add(reset_token)
        await self.session.flush()
        return reset_token

    async def get_by_token(self, token: str) -> Optional[PasswordResetToken]:
        """Get password reset token by token value."""
        token_hash = self._hash_token(token)
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: PasswordResetToken) -> None:
        """Mark token as used."""
        token.used_at = datetime.now(UTC)
        await self.session.flush()

    async def cleanup_expired(self) -> int:
        """Remove expired tokens."""
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.expires_at < datetime.now(UTC))
        )
        expired_tokens = result.scalars().all()

        count = 0
        for token in expired_tokens:
            await self.session.delete(token)
            count += 1

        return count


class EmailVerificationTokenRepository:
    """Repository for EmailVerificationToken model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def create(
        self, user_id: str, token: str, expires_hours: int = 24
    ) -> EmailVerificationToken:
        """Create a new email verification token."""
        token_hash = self._hash_token(token)
        verification_token = EmailVerificationToken(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(hours=expires_hours),
        )
        self.session.add(verification_token)
        await self.session.flush()
        return verification_token

    async def get_by_token(self, token: str) -> Optional[EmailVerificationToken]:
        """Get email verification token by token value."""
        token_hash = self._hash_token(token)
        result = await self.session.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: EmailVerificationToken) -> None:
        """Mark token as used."""
        token.used_at = datetime.now(UTC)
        await self.session.flush()

    async def invalidate_for_user(self, user_id: str) -> None:
        """Invalidate all unused tokens for a user."""
        await self.session.execute(
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )

    async def cleanup_expired(self) -> int:
        """Remove expired tokens."""
        result = await self.session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.expires_at < datetime.now(UTC)
            )
        )
        expired_tokens = result.scalars().all()

        count = 0
        for token in expired_tokens:
            await self.session.delete(token)
            count += 1

        return count


class SavedSearchRepository:
    """Repository for SavedSearchDB model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        name: str,
        filters: dict,
        description: Optional[str] = None,
        alert_frequency: str = "daily",
        notify_on_new: bool = True,
        notify_on_price_drop: bool = True,
    ) -> SavedSearchDB:
        """Create a new saved search."""
        search = SavedSearchDB(
            id=str(uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            filters=filters,
            alert_frequency=alert_frequency,
            notify_on_new=notify_on_new,
            notify_on_price_drop=notify_on_price_drop,
            is_active=True,
        )
        self.session.add(search)
        await self.session.flush()
        return search

    async def get_by_id(self, search_id: str, user_id: str) -> Optional[SavedSearchDB]:
        """Get saved search by ID (scoped to user)."""
        result = await self.session.execute(
            select(SavedSearchDB).where(
                SavedSearchDB.id == search_id, SavedSearchDB.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self, user_id: str, include_inactive: bool = False
    ) -> list[SavedSearchDB]:
        """Get all saved searches for a user."""
        query = select(SavedSearchDB).where(SavedSearchDB.user_id == user_id)
        if not include_inactive:
            query = query.where(SavedSearchDB.is_active == True)  # noqa: E712
        query = query.order_by(SavedSearchDB.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_active(self) -> list[SavedSearchDB]:
        """Get all active saved searches (for scheduler)."""
        result = await self.session.execute(
            select(SavedSearchDB).where(SavedSearchDB.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_frequency(self, frequency: str) -> list[SavedSearchDB]:
        """Get searches by alert frequency (for scheduler)."""
        result = await self.session.execute(
            select(SavedSearchDB).where(
                SavedSearchDB.is_active == True,  # noqa: E712
                SavedSearchDB.alert_frequency == frequency,
            )
        )
        return list(result.scalars().all())

    async def update(self, search: SavedSearchDB, **kwargs) -> SavedSearchDB:
        """Update saved search fields."""
        for key, value in kwargs.items():
            if hasattr(search, key):
                setattr(search, key, value)
        await self.session.flush()
        return search

    async def delete(self, search: SavedSearchDB) -> None:
        """Delete a saved search."""
        await self.session.delete(search)

    async def increment_usage(self, search: SavedSearchDB) -> None:
        """Increment usage count and update last_used_at."""
        search.use_count += 1
        search.last_used_at = datetime.now(UTC)
        await self.session.flush()


class CollectionRepository:
    """Repository for CollectionDB model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        is_default: bool = False,
    ) -> CollectionDB:
        """Create a new collection."""
        collection = CollectionDB(
            id=str(uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            is_default=is_default,
        )
        self.session.add(collection)
        await self.session.flush()
        return collection

    async def get_by_id(self, collection_id: str, user_id: str) -> Optional[CollectionDB]:
        """Get collection by ID (scoped to user)."""
        result = await self.session.execute(
            select(CollectionDB).where(
                CollectionDB.id == collection_id, CollectionDB.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str) -> list[CollectionDB]:
        """Get all collections for a user, ordered by name."""
        result = await self.session.execute(
            select(CollectionDB)
            .where(CollectionDB.user_id == user_id)
            .order_by(CollectionDB.is_default.desc(), CollectionDB.name)
        )
        return list(result.scalars().all())

    async def get_default_collection(self, user_id: str) -> Optional[CollectionDB]:
        """Get user's default collection."""
        result = await self.session.execute(
            select(CollectionDB).where(
                CollectionDB.user_id == user_id,
                CollectionDB.is_default.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_default(self, user_id: str) -> CollectionDB:
        """Get or create default collection for user."""
        collection = await self.get_default_collection(user_id)
        if collection:
            return collection
        return await self.create(
            user_id=user_id,
            name="My Favorites",
            is_default=True,
        )

    async def update(self, collection: CollectionDB, **kwargs) -> CollectionDB:
        """Update collection fields."""
        for key, value in kwargs.items():
            if hasattr(collection, key):
                setattr(collection, key, value)
        await self.session.flush()
        return collection

    async def delete(self, collection: CollectionDB) -> None:
        """Delete a collection (favorites will become uncategorized)."""
        await self.session.delete(collection)

    async def count_favorites(self, collection_id: str) -> int:
        """Count favorites in a collection."""
        result = await self.session.execute(
            select(func.count(FavoriteDB.id)).where(FavoriteDB.collection_id == collection_id)
        )
        return result.scalar() or 0


class FavoriteRepository:
    """Repository for FavoriteDB model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        property_id: str,
        collection_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> FavoriteDB:
        """Create a new favorite."""
        favorite = FavoriteDB(
            id=str(uuid4()),
            user_id=user_id,
            property_id=property_id,
            collection_id=collection_id,
            notes=notes,
        )
        self.session.add(favorite)
        await self.session.flush()
        return favorite

    async def get_by_id(self, favorite_id: str, user_id: str) -> Optional[FavoriteDB]:
        """Get favorite by ID (scoped to user)."""
        result = await self.session.execute(
            select(FavoriteDB).where(FavoriteDB.id == favorite_id, FavoriteDB.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_property(self, user_id: str, property_id: str) -> Optional[FavoriteDB]:
        """Get favorite by property ID (scoped to user)."""
        result = await self.session.execute(
            select(FavoriteDB).where(
                FavoriteDB.user_id == user_id, FavoriteDB.property_id == property_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: str,
        collection_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FavoriteDB]:
        """Get all favorites for a user, optionally filtered by collection."""
        query = select(FavoriteDB).where(FavoriteDB.user_id == user_id)

        if collection_id is not None:
            query = query.where(FavoriteDB.collection_id == collection_id)

        query = query.order_by(FavoriteDB.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str, collection_id: Optional[str] = None) -> int:
        """Count favorites for a user."""
        query = select(func.count(FavoriteDB.id)).where(FavoriteDB.user_id == user_id)
        if collection_id is not None:
            query = query.where(FavoriteDB.collection_id == collection_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_property_ids_by_user(self, user_id: str) -> list[str]:
        """Get all property IDs favorited by a user (for efficient lookup)."""
        result = await self.session.execute(
            select(FavoriteDB.property_id).where(FavoriteDB.user_id == user_id)
        )
        return [row[0] for row in result.all()]

    async def update(self, favorite: FavoriteDB, **kwargs) -> FavoriteDB:
        """Update favorite fields."""
        for key, value in kwargs.items():
            if hasattr(favorite, key):
                setattr(favorite, key, value)
        await self.session.flush()
        return favorite

    async def delete(self, favorite: FavoriteDB) -> None:
        """Delete a favorite."""
        await self.session.delete(favorite)

    async def delete_by_property(self, user_id: str, property_id: str) -> bool:
        """Delete favorite by property ID. Returns True if deleted."""
        favorite = await self.get_by_property(user_id, property_id)
        if favorite:
            await self.delete(favorite)
            return True
        return False

    async def move_to_collection(
        self, user_id: str, property_id: str, collection_id: Optional[str]
    ) -> Optional[FavoriteDB]:
        """Move a favorite to a different collection."""
        favorite = await self.get_by_property(user_id, property_id)
        if favorite:
            favorite.collection_id = collection_id
            await self.session.flush()
        return favorite


class PriceSnapshotRepository:
    """Repository for PriceSnapshot model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        property_id: str,
        price: float,
        price_per_sqm: Optional[float] = None,
        currency: Optional[str] = None,
        source: Optional[str] = None,
    ) -> PriceSnapshot:
        """Create a new price snapshot."""
        snapshot = PriceSnapshot(
            id=str(uuid4()),
            property_id=property_id,
            price=price,
            price_per_sqm=price_per_sqm,
            currency=currency,
            source=source,
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def get_by_property(
        self,
        property_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PriceSnapshot]:
        """Get price history for a property."""
        result = await self.session.execute(
            select(PriceSnapshot)
            .where(PriceSnapshot.property_id == property_id)
            .order_by(PriceSnapshot.recorded_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_for_property(self, property_id: str) -> Optional[PriceSnapshot]:
        """Get the most recent price snapshot for a property."""
        result = await self.session.execute(
            select(PriceSnapshot)
            .where(PriceSnapshot.property_id == property_id)
            .order_by(PriceSnapshot.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_for_property(self, property_id: str) -> int:
        """Count snapshots for a property."""
        result = await self.session.execute(
            select(func.count(PriceSnapshot.id)).where(PriceSnapshot.property_id == property_id)
        )
        return result.scalar() or 0

    async def get_snapshots_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
        property_ids: Optional[list[str]] = None,
    ) -> list[PriceSnapshot]:
        """Get all snapshots in a time period, optionally filtered by property IDs."""
        query = select(PriceSnapshot).where(
            PriceSnapshot.recorded_at >= start_date,
            PriceSnapshot.recorded_at <= end_date,
        )
        if property_ids:
            query = query.where(PriceSnapshot.property_id.in_(property_ids))
        query = query.order_by(PriceSnapshot.recorded_at.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_properties_with_price_drops(
        self,
        threshold_percent: float = 5.0,
        days_back: int = 7,
    ) -> list[dict[str, Any]]:
        """Find properties with price drops exceeding threshold in the past N days."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        # Get recent snapshots ordered by property and date
        result = await self.session.execute(
            select(PriceSnapshot)
            .where(PriceSnapshot.recorded_at >= cutoff_date)
            .order_by(PriceSnapshot.property_id, PriceSnapshot.recorded_at.desc())
        )
        snapshots = result.scalars().all()

        # Group by property and detect drops
        property_prices: dict[str, list[PriceSnapshot]] = {}
        for snap in snapshots:
            if snap.property_id not in property_prices:
                property_prices[snap.property_id] = []
            property_prices[snap.property_id].append(snap)

        drops = []
        for prop_id, snaps in property_prices.items():
            if len(snaps) >= 2:
                # Compare most recent to oldest in the period
                latest = snaps[0]  # Most recent (first due to desc order)
                oldest = snaps[-1]  # Oldest (last in the list)
                if oldest.price > 0:
                    change_pct = ((oldest.price - latest.price) / oldest.price) * 100
                    if change_pct >= threshold_percent:
                        drops.append(
                            {
                                "property_id": prop_id,
                                "old_price": oldest.price,
                                "new_price": latest.price,
                                "percent_drop": change_pct,
                                "recorded_at": latest.recorded_at,
                            }
                        )

        return drops

    async def cleanup_old_snapshots(self, days_to_keep: int = 365) -> int:
        """Remove snapshots older than specified days."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)
        result = await self.session.execute(
            select(PriceSnapshot).where(PriceSnapshot.recorded_at < cutoff_date)
        )
        old_snapshots = result.scalars().all()

        count = 0
        for snapshot in old_snapshots:
            await self.session.delete(snapshot)
            count += 1

        return count


class AnomalyRepository:
    """Repository for MarketAnomaly model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        anomaly_type: str,
        severity: str,
        scope_type: str,
        scope_id: str,
        algorithm: str,
        threshold_used: float,
        metric_name: str,
        expected_value: float,
        actual_value: float,
        deviation_percent: float,
        z_score: Optional[float] = None,
        baseline_period_start: Optional[datetime] = None,
        baseline_period_end: Optional[datetime] = None,
        comparison_period_start: Optional[datetime] = None,
        comparison_period_end: Optional[datetime] = None,
        context: Optional[dict] = None,
    ):
        """Create a new market anomaly record."""
        from db.models import MarketAnomaly

        anomaly = MarketAnomaly(
            id=str(uuid4()),
            anomaly_type=anomaly_type,
            severity=severity,
            scope_type=scope_type,
            scope_id=scope_id,
            algorithm=algorithm,
            threshold_used=threshold_used,
            metric_name=metric_name,
            expected_value=expected_value,
            actual_value=actual_value,
            deviation_percent=deviation_percent,
            z_score=z_score,
            baseline_period_start=baseline_period_start,
            baseline_period_end=baseline_period_end,
            comparison_period_start=comparison_period_start,
            comparison_period_end=comparison_period_end,
            context=context or {},
        )
        self.session.add(anomaly)
        await self.session.flush()
        return anomaly

    async def get_by_id(self, anomaly_id: str):
        """Get anomaly by ID."""
        result = await self.session.execute(
            select(MarketAnomaly).where(MarketAnomaly.id == anomaly_id)
        )
        return result.scalar_one_or_none()

    async def get_by_scope(
        self,
        scope_type: str,
        scope_id: str,
        limit: int = 50,
        offset: int = 0,
    ):
        """Get anomalies for a specific scope (e.g., property, city, district)."""
        result = await self.session.execute(
            select(MarketAnomaly)
            .where(MarketAnomaly.scope_type == scope_type, MarketAnomaly.scope_id == scope_id)
            .order_by(MarketAnomaly.detected_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        limit: int = 50,
        severity_filter: Optional[str] = None,
        anomaly_type_filter: Optional[str] = None,
    ):
        """Get recent anomalies, optional filters."""
        query = select(MarketAnomaly)

        if severity_filter:
            query = query.where(MarketAnomaly.severity == severity_filter)
        if anomaly_type_filter:
            query = query.where(MarketAnomaly.anomaly_type == anomaly_type_filter)

        query = query.order_by(MarketAnomaly.detected_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_undismissed_count(self) -> int:
        """Count undismissed anomalies."""
        result = await self.session.execute(
            select(func.count(MarketAnomaly.id)).where(MarketAnomaly.dismissed_at.is_(None))
        )
        return result.scalar() or 0

    async def mark_alert_sent(self, anomaly_id: str) -> None:
        """Mark that an alert has been sent for this anomaly."""
        await self.session.execute(
            update(MarketAnomaly)
            .where(MarketAnomaly.id == anomaly_id)
            .values(alert_sent=True, alert_sent_at=datetime.now(UTC))
        )

    async def dismiss(self, anomaly_id: str, dismissed_by: Optional[str] = None) -> None:
        """Dismiss an anomaly."""
        await self.session.execute(
            update(MarketAnomaly)
            .where(MarketAnomaly.id == anomaly_id)
            .values(dismissed_at=datetime.now(UTC), dismissed_by=dismissed_by)
        )

    async def get_stats(self) -> dict[str, Any]:
        """Get anomaly statistics."""
        # Total count
        total_result = await self.session.execute(select(func.count(MarketAnomaly.id)))
        total = total_result.scalar() or 0

        # Count by severity
        severity_result = await self.session.execute(
            select(MarketAnomaly.severity, func.count(MarketAnomaly.id)).group_by(
                MarketAnomaly.severity
            )
        )
        severity_counts = {row.severity: row.count for row in severity_result}

        # Count by type
        type_result = await self.session.execute(
            select(MarketAnomaly.anomaly_type, func.count(MarketAnomaly.id)).group_by(
                MarketAnomaly.anomaly_type
            )
        )
        type_counts = {row.anomaly_type: row.count for row in type_result}

        # Undismissed count
        undismissed = await self.get_undismissed_count()

        return {
            "total": total,
            "by_severity": severity_counts,
            "by_type": type_counts,
            "undismissed": undismissed,
        }


class LeadRepository:
    """Repository for Lead model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        visitor_id: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        source: Optional[str] = None,
        consent_given: bool = False,
    ) -> Lead:
        """Create a new lead."""
        lead = Lead(
            id=str(uuid4()),
            visitor_id=visitor_id,
            user_id=user_id,
            email=email.lower().strip() if email else None,
            phone=phone,
            name=name,
            source=source,
            consent_given=consent_given,
            consent_at=datetime.now(UTC) if consent_given else None,
            first_seen_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
        )
        self.session.add(lead)
        await self.session.flush()
        return lead

    async def get_by_id(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID."""
        result = await self.session.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalar_one_or_none()

    async def get_by_visitor_id(self, visitor_id: str) -> Optional[Lead]:
        """Get lead by visitor ID (cookie UUID)."""
        result = await self.session.execute(select(Lead).where(Lead.visitor_id == visitor_id))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> Optional[Lead]:
        """Get lead by linked user ID."""
        result = await self.session.execute(select(Lead).where(Lead.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Lead]:
        """Get lead by email address."""
        result = await self.session.execute(select(Lead).where(Lead.email == email.lower().strip()))
        return result.scalar_one_or_none()

    async def update(self, lead: Lead, **kwargs) -> Lead:
        """Update lead fields."""
        for key, value in kwargs.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
        await self.session.flush()
        return lead

    async def update_last_activity(self, lead: Lead) -> None:
        """Update lead's last activity timestamp."""
        lead.last_activity_at = datetime.now(UTC)
        await self.session.flush()

    async def update_score(self, lead: Lead, score: int) -> None:
        """Update lead's current score (denormalized)."""
        lead.current_score = score
        await self.session.flush()

    async def link_to_user(self, lead: Lead, user_id: str) -> Lead:
        """Link an anonymous lead to a registered user."""
        lead.user_id = user_id
        await self.session.flush()
        return lead

    async def set_consent(self, lead: Lead, consent_given: bool = True) -> Lead:
        """Set GDPR consent for lead."""
        lead.consent_given = consent_given
        lead.consent_at = datetime.now(UTC) if consent_given else None
        await self.session.flush()
        return lead

    async def get_list(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        score_min: Optional[int] = None,
        score_max: Optional[int] = None,
        has_email: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "score",
        sort_order: str = "desc",
    ) -> list[Lead]:
        """Get filtered list of leads."""
        query = select(Lead)

        # Filter by assigned agent
        if agent_id:
            query = query.join(AgentAssignment).where(
                AgentAssignment.agent_id == agent_id,
                AgentAssignment.is_active == True,  # noqa: E712
            )

        # Apply filters
        if status:
            query = query.where(Lead.status == status)
        if score_min is not None:
            query = query.where(Lead.current_score >= score_min)
        if score_max is not None:
            query = query.where(Lead.current_score <= score_max)
        if has_email is True:
            query = query.where(Lead.email.isnot(None))
        elif has_email is False:
            query = query.where(Lead.email.is_(None))

        # Apply sorting
        sort_column = {
            "score": Lead.current_score,
            "last_activity": Lead.last_activity_at,
            "created_at": Lead.created_at,
            "name": Lead.name,
        }.get(sort_by, Lead.current_score)

        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        score_min: Optional[int] = None,
        score_max: Optional[int] = None,
        has_email: Optional[bool] = None,
    ) -> int:
        """Count leads matching filters."""
        query = select(func.count(Lead.id))

        if agent_id:
            query = query.join(AgentAssignment).where(
                AgentAssignment.agent_id == agent_id,
                AgentAssignment.is_active == True,  # noqa: E712
            )

        if status:
            query = query.where(Lead.status == status)
        if score_min is not None:
            query = query.where(Lead.current_score >= score_min)
        if score_max is not None:
            query = query.where(Lead.current_score <= score_max)
        if has_email is True:
            query = query.where(Lead.email.isnot(None))
        elif has_email is False:
            query = query.where(Lead.email.is_(None))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_high_scoring(
        self,
        threshold: int = 70,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[Lead]:
        """Get leads with score above threshold (for notifications)."""
        query = select(Lead).where(Lead.current_score >= threshold)

        if since:
            query = query.where(Lead.updated_at >= since)

        query = query.order_by(Lead.current_score.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_or_create_by_visitor_id(self, visitor_id: str) -> Lead:
        """Get existing lead or create new one by visitor ID."""
        lead = await self.get_by_visitor_id(visitor_id)
        if lead:
            return lead
        return await self.create(visitor_id=visitor_id)

    async def delete(self, lead: Lead) -> None:
        """Delete a lead (GDPR right to be forgotten)."""
        await self.session.delete(lead)


class LeadInteractionRepository:
    """Repository for LeadInteraction model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        lead_id: str,
        interaction_type: str,
        property_id: Optional[str] = None,
        search_query: Optional[str] = None,
        metadata: Optional[dict] = None,
        session_id: Optional[str] = None,
        page_url: Optional[str] = None,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        time_spent_seconds: Optional[int] = None,
    ) -> LeadInteraction:
        """Record a lead interaction."""
        interaction = LeadInteraction(
            id=str(uuid4()),
            lead_id=lead_id,
            interaction_type=interaction_type,
            property_id=property_id,
            search_query=search_query,
            interaction_metadata=metadata or {},
            session_id=session_id,
            page_url=page_url,
            referrer=referrer,
            user_agent=user_agent,
            ip_address=ip_address,
            time_spent_seconds=time_spent_seconds,
        )
        self.session.add(interaction)
        await self.session.flush()
        return interaction

    async def get_by_lead(
        self,
        lead_id: str,
        limit: int = 100,
        offset: int = 0,
        interaction_type: Optional[str] = None,
    ) -> list[LeadInteraction]:
        """Get interactions for a lead."""
        query = select(LeadInteraction).where(LeadInteraction.lead_id == lead_id)

        if interaction_type:
            query = query.where(LeadInteraction.interaction_type == interaction_type)

        query = query.order_by(LeadInteraction.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_lead(
        self,
        lead_id: str,
        interaction_type: Optional[str] = None,
    ) -> int:
        """Count interactions for a lead."""
        query = select(func.count(LeadInteraction.id)).where(LeadInteraction.lead_id == lead_id)

        if interaction_type:
            query = query.where(LeadInteraction.interaction_type == interaction_type)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_interaction_stats(self, lead_id: str) -> dict[str, Any]:
        """Get aggregated interaction statistics for a lead."""
        # Count by type
        type_counts_result = await self.session.execute(
            select(
                LeadInteraction.interaction_type,
                func.count(LeadInteraction.id).label("count"),
            )
            .where(LeadInteraction.lead_id == lead_id)
            .group_by(LeadInteraction.interaction_type)
        )
        type_counts = {row.interaction_type: row.count for row in type_counts_result}

        # Total time spent
        time_result = await self.session.execute(
            select(func.sum(LeadInteraction.time_spent_seconds)).where(
                LeadInteraction.lead_id == lead_id,
                LeadInteraction.time_spent_seconds.isnot(None),
            )
        )
        total_time = time_result.scalar() or 0

        # Unique properties viewed
        props_result = await self.session.execute(
            select(func.count(func.distinct(LeadInteraction.property_id))).where(
                LeadInteraction.lead_id == lead_id,
                LeadInteraction.property_id.isnot(None),
            )
        )
        unique_properties = props_result.scalar() or 0

        # Unique searches
        searches_result = await self.session.execute(
            select(func.count(func.distinct(LeadInteraction.search_query))).where(
                LeadInteraction.lead_id == lead_id,
                LeadInteraction.search_query.isnot(None),
            )
        )
        unique_searches = searches_result.scalar() or 0

        # First and last activity
        first_result = await self.session.execute(
            select(func.min(LeadInteraction.created_at)).where(LeadInteraction.lead_id == lead_id)
        )
        first_activity = first_result.scalar()

        last_result = await self.session.execute(
            select(func.max(LeadInteraction.created_at)).where(LeadInteraction.lead_id == lead_id)
        )
        last_activity = last_result.scalar()

        return {
            "type_counts": type_counts,
            "total_time_spent_seconds": total_time,
            "unique_properties_viewed": unique_properties,
            "unique_searches": unique_searches,
            "first_activity_at": first_activity,
            "last_activity_at": last_activity,
            "total_interactions": sum(type_counts.values()),
        }

    async def get_recent_searches(self, lead_id: str, limit: int = 10) -> list[str]:
        """Get recent search queries for a lead."""
        result = await self.session.execute(
            select(LeadInteraction.search_query)
            .where(
                LeadInteraction.lead_id == lead_id,
                LeadInteraction.interaction_type == "search",
                LeadInteraction.search_query.isnot(None),
            )
            .order_by(LeadInteraction.created_at.desc())
            .limit(limit)
        )
        return [row.search_query for row in result if row.search_query]

    async def get_recent_properties(self, lead_id: str, limit: int = 10) -> list[str]:
        """Get recently viewed property IDs for a lead."""
        result = await self.session.execute(
            select(LeadInteraction.property_id)
            .where(
                LeadInteraction.lead_id == lead_id,
                LeadInteraction.interaction_type == "view",
                LeadInteraction.property_id.isnot(None),
            )
            .order_by(LeadInteraction.created_at.desc())
            .limit(limit)
        )
        return [row.property_id for row in result if row.property_id]

    async def cleanup_old_interactions(self, days_to_keep: int = 365) -> int:
        """Remove interactions older than specified days."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)
        result = await self.session.execute(
            select(LeadInteraction).where(LeadInteraction.created_at < cutoff_date)
        )
        old_interactions = result.scalars().all()

        count = 0
        for interaction in old_interactions:
            await self.session.delete(interaction)
            count += 1

        return count


class LeadScoreRepository:
    """Repository for LeadScore model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        lead_id: str,
        total_score: int,
        search_activity_score: int,
        engagement_score: int,
        intent_score: int,
        score_factors: dict,
        recommendations: Optional[list[str]] = None,
        model_version: str = "1.0.0",
    ) -> LeadScore:
        """Create a new lead score record."""
        score = LeadScore(
            id=str(uuid4()),
            lead_id=lead_id,
            total_score=total_score,
            search_activity_score=search_activity_score,
            engagement_score=engagement_score,
            intent_score=intent_score,
            score_factors=score_factors,
            recommendations=recommendations,
            model_version=model_version,
        )
        self.session.add(score)
        await self.session.flush()
        return score

    async def get_latest_for_lead(self, lead_id: str) -> Optional[LeadScore]:
        """Get the most recent score for a lead."""
        result = await self.session.execute(
            select(LeadScore)
            .where(LeadScore.lead_id == lead_id)
            .order_by(LeadScore.calculated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history_for_lead(
        self,
        lead_id: str,
        limit: int = 30,
    ) -> list[LeadScore]:
        """Get score history for a lead."""
        result = await self.session.execute(
            select(LeadScore)
            .where(LeadScore.lead_id == lead_id)
            .order_by(LeadScore.calculated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_leads_needing_recalc(
        self,
        max_age_hours: int = 24,
        limit: int = 100,
    ) -> list[str]:
        """Get lead IDs whose scores need recalculation."""
        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)

        # Find leads where latest score is older than cutoff or no score exists
        result = await self.session.execute(
            select(Lead.id)
            .outerjoin(LeadScore, Lead.id == LeadScore.lead_id)
            .where((LeadScore.calculated_at.is_(None)) | (LeadScore.calculated_at < cutoff))
            .distinct()
            .limit(limit)
        )
        return [row.id for row in result]

    async def count_scores_today(self) -> int:
        """Count scores calculated today."""
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(LeadScore.id)).where(LeadScore.calculated_at >= today_start)
        )
        return result.scalar() or 0


class AgentAssignmentRepository:
    """Repository for AgentAssignment model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        lead_id: str,
        agent_id: str,
        assigned_by: Optional[str] = None,
        notes: Optional[str] = None,
        is_primary: bool = False,
    ) -> AgentAssignment:
        """Create a new agent assignment."""
        assignment = AgentAssignment(
            id=str(uuid4()),
            lead_id=lead_id,
            agent_id=agent_id,
            assigned_by=assigned_by,
            notes=notes,
            is_primary=is_primary,
        )
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def get_by_id(self, assignment_id: str) -> Optional[AgentAssignment]:
        """Get assignment by ID."""
        result = await self.session.execute(
            select(AgentAssignment).where(AgentAssignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def get_active_for_lead(self, lead_id: str) -> list[AgentAssignment]:
        """Get all active assignments for a lead."""
        result = await self.session.execute(
            select(AgentAssignment)
            .where(
                AgentAssignment.lead_id == lead_id,
                AgentAssignment.is_active == True,  # noqa: E712
            )
            .order_by(AgentAssignment.is_primary.desc(), AgentAssignment.assigned_at.desc())
        )
        return list(result.scalars().all())

    async def get_primary_for_lead(self, lead_id: str) -> Optional[AgentAssignment]:
        """Get primary agent assignment for a lead."""
        result = await self.session.execute(
            select(AgentAssignment).where(
                AgentAssignment.lead_id == lead_id,
                AgentAssignment.is_primary == True,  # noqa: E712
                AgentAssignment.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_leads_for_agent(
        self,
        agent_id: str,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentAssignment]:
        """Get all assignments for an agent."""
        query = select(AgentAssignment).where(AgentAssignment.agent_id == agent_id)

        if active_only:
            query = query.where(AgentAssignment.is_active == True)  # noqa: E712

        query = query.order_by(AgentAssignment.assigned_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def set_primary(self, assignment_id: str) -> None:
        """Set an assignment as primary (unsets other primaries for the lead)."""
        assignment = await self.get_by_id(assignment_id)
        if assignment:
            # Unset other primaries for this lead
            await self.session.execute(
                update(AgentAssignment)
                .where(
                    AgentAssignment.lead_id == assignment.lead_id,
                    AgentAssignment.id != assignment_id,
                )
                .values(is_primary=False)
            )
            # Set this one as primary
            assignment.is_primary = True
            await self.session.flush()

    async def unassign(self, assignment_id: str, unassigned_by: Optional[str] = None) -> None:
        """Deactivate an assignment."""
        await self.session.execute(
            update(AgentAssignment)
            .where(AgentAssignment.id == assignment_id)
            .values(
                is_active=False,
                unassigned_at=datetime.now(UTC),
                unassigned_by=unassigned_by,
            )
        )

    async def assign_lead_to_agent(
        self,
        lead_id: str,
        agent_id: str,
        assigned_by: Optional[str] = None,
        notes: Optional[str] = None,
        is_primary: bool = True,
    ) -> AgentAssignment:
        """Assign a lead to an agent, handling primary status."""
        # Check if already assigned
        existing = await self.get_primary_for_lead(lead_id)
        if existing and existing.agent_id == agent_id:
            return existing

        # If setting as primary, unset existing primary
        if is_primary:
            await self.session.execute(
                update(AgentAssignment)
                .where(
                    AgentAssignment.lead_id == lead_id,
                    AgentAssignment.is_primary == True,  # noqa: E712
                )
                .values(is_primary=False)
            )

        return await self.create(
            lead_id=lead_id,
            agent_id=agent_id,
            assigned_by=assigned_by,
            notes=notes,
            is_primary=is_primary,
        )

    async def count_for_agent(self, agent_id: str, active_only: bool = True) -> int:
        """Count assignments for an agent."""
        query = select(func.count(AgentAssignment.id)).where(AgentAssignment.agent_id == agent_id)

        if active_only:
            query = query.where(AgentAssignment.is_active == True)  # noqa: E712

        result = await self.session.execute(query)
        return result.scalar() or 0


class PushSubscriptionRepository:
    """Repository for push notification subscriptions (Task #63)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> PushSubscription:
        """Create a new push subscription."""
        subscription = PushSubscription(
            id=str(uuid4()),
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent,
            device_name=device_name,
        )
        self.session.add(subscription)
        await self.session.flush()
        return subscription

    async def get_by_id(self, subscription_id: str) -> Optional[PushSubscription]:
        """Get subscription by ID."""
        result = await self.session.execute(
            select(PushSubscription).where(PushSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def get_by_endpoint(self, endpoint: str) -> Optional[PushSubscription]:
        """Get subscription by endpoint URL."""
        result = await self.session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str, active_only: bool = True) -> list[PushSubscription]:
        """Get all subscriptions for a user."""
        query = select(PushSubscription).where(PushSubscription.user_id == user_id)
        if active_only:
            query = query.where(PushSubscription.is_active == True)  # noqa: E712
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, subscription: PushSubscription, **kwargs) -> PushSubscription:
        """Update subscription fields."""
        for key, value in kwargs.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)
        await self.session.flush()
        return subscription

    async def deactivate(self, subscription: PushSubscription) -> None:
        """Deactivate a subscription."""
        subscription.is_active = False
        await self.session.flush()

    async def delete(self, subscription: PushSubscription) -> None:
        """Delete a subscription."""
        await self.session.delete(subscription)

    async def delete_by_endpoint(self, endpoint: str) -> bool:
        """Delete subscription by endpoint. Returns True if deleted."""
        subscription = await self.get_by_endpoint(endpoint)
        if subscription:
            await self.session.delete(subscription)
            return True
        return False

    async def count_for_user(self, user_id: str, active_only: bool = True) -> int:
        """Count subscriptions for a user."""
        query = select(func.count(PushSubscription.id)).where(PushSubscription.user_id == user_id)
        if active_only:
            query = query.where(PushSubscription.is_active == True)  # noqa: E712
        result = await self.session.execute(query)
        return result.scalar() or 0


# =============================================================================
# Agent/Broker System Repositories (Task #45)
# =============================================================================


class AgentProfileRepository:
    """Repository for agent profile operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        agency_name: Optional[str] = None,
        agency_id: Optional[str] = None,
        license_number: Optional[str] = None,
        license_state: Optional[str] = None,
        professional_email: Optional[str] = None,
        professional_phone: Optional[str] = None,
        office_address: Optional[str] = None,
        specialties: Optional[list[str]] = None,
        service_areas: Optional[list[str]] = None,
        property_types: Optional[list[str]] = None,
        languages: Optional[list[str]] = None,
        bio: Optional[str] = None,
        profile_image_url: Optional[str] = None,
    ) -> AgentProfile:
        """Create a new agent profile."""
        profile = AgentProfile(
            id=str(uuid4()),
            user_id=user_id,
            agency_name=agency_name,
            agency_id=agency_id,
            license_number=license_number,
            license_state=license_state,
            professional_email=professional_email,
            professional_phone=professional_phone,
            office_address=office_address,
            specialties=specialties or [],
            service_areas=service_areas or [],
            property_types=property_types or [],
            languages=languages or [],
            bio=bio,
            profile_image_url=profile_image_url,
            is_verified=False,
            is_active=True,
        )
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def get_by_id(self, profile_id: str) -> Optional[AgentProfile]:
        """Get agent profile by ID."""
        result = await self.session.execute(
            select(AgentProfile).where(AgentProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> Optional[AgentProfile]:
        """Get agent profile by user ID."""
        result = await self.session.execute(
            select(AgentProfile).where(AgentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        city: Optional[str] = None,
        specialty: Optional[str] = None,
        property_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        agency_id: Optional[str] = None,
        is_verified: Optional[bool] = None,
        language: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "rating",
        sort_order: str = "desc",
    ) -> list[AgentProfile]:
        """Get list of agent profiles with filters."""
        query = select(AgentProfile).where(AgentProfile.is_active == True)  # noqa: E712

        # Apply filters
        if is_verified is not None:
            query = query.where(AgentProfile.is_verified == is_verified)
        if min_rating is not None:
            query = query.where(AgentProfile.average_rating >= min_rating)
        if agency_id is not None:
            query = query.where(AgentProfile.agency_id == agency_id)
        if city:
            # Filter by service area (JSON array contains)
            query = query.where(AgentProfile.service_areas.contains([city]))
        if specialty:
            query = query.where(AgentProfile.specialties.contains([specialty]))
        if property_type:
            query = query.where(AgentProfile.property_types.contains([property_type]))
        if language:
            query = query.where(AgentProfile.languages.contains([language]))

        # Apply sorting
        sort_column = getattr(AgentProfile, sort_by, AgentProfile.average_rating)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        city: Optional[str] = None,
        specialty: Optional[str] = None,
        property_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        agency_id: Optional[str] = None,
        is_verified: Optional[bool] = None,
        language: Optional[str] = None,
    ) -> int:
        """Count agent profiles with filters."""
        query = select(func.count(AgentProfile.id)).where(AgentProfile.is_active == True)  # noqa: E712

        if is_verified is not None:
            query = query.where(AgentProfile.is_verified == is_verified)
        if min_rating is not None:
            query = query.where(AgentProfile.average_rating >= min_rating)
        if agency_id is not None:
            query = query.where(AgentProfile.agency_id == agency_id)
        if city:
            query = query.where(AgentProfile.service_areas.contains([city]))
        if specialty:
            query = query.where(AgentProfile.specialties.contains([specialty]))
        if property_type:
            query = query.where(AgentProfile.property_types.contains([property_type]))
        if language:
            query = query.where(AgentProfile.languages.contains([language]))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update(self, profile: AgentProfile, **kwargs) -> AgentProfile:
        """Update agent profile fields."""
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        await self.session.flush()
        return profile

    async def update_rating(self, profile: AgentProfile, new_rating: float) -> None:
        """Recalculate average rating after new review."""
        # This would typically be called after adding/removing a review
        profile.average_rating = new_rating
        await self.session.flush()

    async def increment_reviews(self, profile: AgentProfile) -> None:
        """Increment total reviews count."""
        profile.total_reviews += 1
        await self.session.flush()

    async def increment_sales(self, profile: AgentProfile) -> None:
        """Increment total sales count."""
        profile.total_sales += 1
        await self.session.flush()

    async def verify(self, profile: AgentProfile) -> None:
        """Verify an agent profile."""
        profile.is_verified = True
        profile.verification_date = datetime.now(UTC)
        await self.session.flush()

    async def delete(self, profile: AgentProfile) -> None:
        """Delete an agent profile (soft delete by setting is_active=False)."""
        profile.is_active = False
        await self.session.flush()


class AgentListingRepository:
    """Repository for agent listing operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        agent_id: str,
        property_id: str,
        listing_type: str = "sale",
        is_primary: bool = False,
        commission_rate: Optional[float] = None,
    ) -> AgentListing:
        """Create a new agent listing."""
        listing = AgentListing(
            id=str(uuid4()),
            agent_id=agent_id,
            property_id=property_id,
            listing_type=listing_type,
            is_primary=is_primary,
            is_active=True,
            commission_rate=commission_rate,
        )
        self.session.add(listing)
        await self.session.flush()
        return listing

    async def get_by_id(self, listing_id: str) -> Optional[AgentListing]:
        """Get listing by ID."""
        result = await self.session.execute(
            select(AgentListing).where(AgentListing.id == listing_id)
        )
        return result.scalar_one_or_none()

    async def get_by_agent(
        self,
        agent_id: str,
        listing_type: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentListing]:
        """Get listings for an agent."""
        query = select(AgentListing).where(AgentListing.agent_id == agent_id)
        if active_only:
            query = query.where(AgentListing.is_active == True)  # noqa: E712
        if listing_type:
            query = query.where(AgentListing.listing_type == listing_type)
        query = query.order_by(AgentListing.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_property(
        self,
        property_id: str,
        active_only: bool = True,
    ) -> list[AgentListing]:
        """Get all agents for a property."""
        query = select(AgentListing).where(AgentListing.property_id == property_id)
        if active_only:
            query = query.where(AgentListing.is_active.is_(True))
        query = query.where(AgentListing.is_primary.is_(True))  # Primary first
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_for_agent(self, agent_id: str, active_only: bool = True) -> int:
        """Count listings for an agent."""
        query = select(func.count(AgentListing.id)).where(AgentListing.agent_id == agent_id)
        if active_only:
            query = query.where(AgentListing.is_active == True)  # noqa: E712
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def set_primary(self, listing: AgentListing) -> None:
        """Set a listing as primary (unsets others for same property)."""
        # First unset all primary for this property
        await self.session.execute(
            update(AgentListing)
            .where(AgentListing.property_id == listing.property_id)
            .where(AgentListing.agent_id == listing.agent_id)
            .values(is_primary=False)
        )
        listing.is_primary = True
        await self.session.flush()

    async def deactivate(self, listing: AgentListing) -> None:
        """Deactivate a listing."""
        listing.is_active = False
        await self.session.flush()

    async def delete(self, listing: AgentListing) -> None:
        """Delete a listing."""
        await self.session.delete(listing)


class AgentInquiryRepository:
    """Repository for agent inquiry operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        agent_id: str,
        name: str,
        email: str,
        inquiry_type: str,
        message: str,
        user_id: Optional[str] = None,
        visitor_id: Optional[str] = None,
        phone: Optional[str] = None,
        property_id: Optional[str] = None,
    ) -> AgentInquiry:
        """Create a new inquiry."""
        inquiry = AgentInquiry(
            id=str(uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            visitor_id=visitor_id,
            name=name,
            email=email,
            phone=phone,
            property_id=property_id,
            inquiry_type=inquiry_type,
            message=message,
            status="new",
        )
        self.session.add(inquiry)
        await self.session.flush()
        return inquiry

    async def get_by_id(self, inquiry_id: str) -> Optional[AgentInquiry]:
        """Get inquiry by ID."""
        result = await self.session.execute(
            select(AgentInquiry).where(AgentInquiry.id == inquiry_id)
        )
        return result.scalar_one_or_none()

    async def get_by_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
        inquiry_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentInquiry]:
        """Get inquiries for an agent."""
        query = select(AgentInquiry).where(AgentInquiry.agent_id == agent_id)
        if status:
            query = query.where(AgentInquiry.status == status)
        if inquiry_type:
            query = query.where(AgentInquiry.inquiry_type == inquiry_type)
        query = query.order_by(AgentInquiry.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_for_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
    ) -> int:
        """Count inquiries for an agent."""
        query = select(func.count(AgentInquiry.id)).where(AgentInquiry.agent_id == agent_id)
        if status:
            query = query.where(AgentInquiry.status == status)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def mark_read(self, inquiry: AgentInquiry) -> None:
        """Mark inquiry as read."""
        inquiry.status = "read"
        inquiry.read_at = datetime.now(UTC)
        await self.session.flush()

    async def mark_responded(self, inquiry: AgentInquiry) -> None:
        """Mark inquiry as responded."""
        inquiry.status = "responded"
        inquiry.responded_at = datetime.now(UTC)
        await self.session.flush()

    async def update_status(self, inquiry: AgentInquiry, status: str) -> None:
        """Update inquiry status."""
        inquiry.status = status
        await self.session.flush()

    async def delete(self, inquiry: AgentInquiry) -> None:
        """Delete an inquiry."""
        await self.session.delete(inquiry)


class ViewingAppointmentRepository:
    """Repository for viewing appointment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        agent_id: str,
        property_id: str,
        proposed_datetime: datetime,
        client_name: str,
        client_email: str,
        user_id: Optional[str] = None,
        visitor_id: Optional[str] = None,
        client_phone: Optional[str] = None,
        duration_minutes: int = 60,
        notes: Optional[str] = None,
    ) -> ViewingAppointment:
        """Create a new viewing appointment request."""
        appointment = ViewingAppointment(
            id=str(uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            visitor_id=visitor_id,
            client_name=client_name,
            client_email=client_email,
            client_phone=client_phone,
            property_id=property_id,
            proposed_datetime=proposed_datetime,
            duration_minutes=duration_minutes,
            notes=notes,
            status="requested",
        )
        self.session.add(appointment)
        await self.session.flush()
        return appointment

    async def get_by_id(self, appointment_id: str) -> Optional[ViewingAppointment]:
        """Get appointment by ID."""
        result = await self.session.execute(
            select(ViewingAppointment).where(ViewingAppointment.id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ViewingAppointment]:
        """Get appointments for an agent."""
        query = select(ViewingAppointment).where(ViewingAppointment.agent_id == agent_id)
        if status:
            query = query.where(ViewingAppointment.status == status)
        if from_date:
            query = query.where(ViewingAppointment.proposed_datetime >= from_date)
        if to_date:
            query = query.where(ViewingAppointment.proposed_datetime <= to_date)
        query = (
            query.order_by(ViewingAppointment.proposed_datetime.asc()).offset(offset).limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[ViewingAppointment]:
        """Get appointments for a user (client)."""
        query = select(ViewingAppointment).where(ViewingAppointment.user_id == user_id)
        if status:
            query = query.where(ViewingAppointment.status == status)
        query = query.order_by(ViewingAppointment.proposed_datetime.asc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_for_agent(
        self,
        agent_id: str,
        status: Optional[str] = None,
    ) -> int:
        """Count appointments for an agent."""
        query = select(func.count(ViewingAppointment.id)).where(
            ViewingAppointment.agent_id == agent_id
        )
        if status:
            query = query.where(ViewingAppointment.status == status)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def confirm(
        self, appointment: ViewingAppointment, confirmed_datetime: Optional[datetime] = None
    ) -> None:
        """Confirm an appointment."""
        appointment.status = "confirmed"
        appointment.confirmed_datetime = confirmed_datetime or appointment.proposed_datetime
        await self.session.flush()

    async def cancel(self, appointment: ViewingAppointment, reason: Optional[str] = None) -> None:
        """Cancel an appointment."""
        appointment.status = "cancelled"
        appointment.cancellation_reason = reason
        await self.session.flush()

    async def complete(self, appointment: ViewingAppointment) -> None:
        """Mark appointment as completed."""
        appointment.status = "completed"
        await self.session.flush()

    async def update(self, appointment: ViewingAppointment, **kwargs) -> ViewingAppointment:
        """Update appointment fields."""
        for key, value in kwargs.items():
            if hasattr(appointment, key):
                setattr(appointment, key, value)
        await self.session.flush()
        return appointment

    async def delete(self, appointment: ViewingAppointment) -> None:
        """Delete an appointment."""
        await self.session.delete(appointment)


class DocumentRepository:
    """Repository for DocumentDB model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        filename: str,
        original_filename: str,
        storage_path: str,
        file_type: str,
        file_size: int,
        property_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        description: Optional[str] = None,
        expiry_date: Optional[datetime] = None,
    ) -> DocumentDB:
        """Create a new document record."""
        import json

        document = DocumentDB(
            id=str(uuid4()),
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            storage_path=storage_path,
            file_type=file_type,
            file_size=file_size,
            property_id=property_id,
            category=category,
            tags=json.dumps(tags) if tags else None,
            description=description,
            expiry_date=expiry_date,
            ocr_status="pending",
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def get_by_id(self, document_id: str, user_id: str) -> Optional[DocumentDB]:
        """Get document by ID (scoped to user)."""
        result = await self.session.execute(
            select(DocumentDB).where(DocumentDB.id == document_id, DocumentDB.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_unscoped(self, document_id: str) -> Optional[DocumentDB]:
        """Get document by ID without user scoping (for admin/internal use)."""
        result = await self.session.execute(select(DocumentDB).where(DocumentDB.id == document_id))
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: str,
        property_id: Optional[str] = None,
        category: Optional[str] = None,
        ocr_status: Optional[str] = None,
        tags: Optional[list[str]] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[DocumentDB]:
        """Get documents for a user with optional filters."""
        query = select(DocumentDB).where(DocumentDB.user_id == user_id)

        if property_id:
            query = query.where(DocumentDB.property_id == property_id)
        if category:
            query = query.where(DocumentDB.category == category)
        if ocr_status:
            query = query.where(DocumentDB.ocr_status == ocr_status)
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                (DocumentDB.original_filename.ilike(search_pattern))
                | (DocumentDB.description.ilike(search_pattern))
            )

        # Sorting
        sort_column = getattr(DocumentDB, sort_by, DocumentDB.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: str,
        property_id: Optional[str] = None,
        category: Optional[str] = None,
        ocr_status: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """Count documents for a user with optional filters."""
        query = select(func.count(DocumentDB.id)).where(DocumentDB.user_id == user_id)

        if property_id:
            query = query.where(DocumentDB.property_id == property_id)
        if category:
            query = query.where(DocumentDB.category == category)
        if ocr_status:
            query = query.where(DocumentDB.ocr_status == ocr_status)
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                (DocumentDB.original_filename.ilike(search_pattern))
                | (DocumentDB.description.ilike(search_pattern))
            )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_by_user_simple(self, user_id: str) -> int:
        """Simple count of all documents for a user."""
        result = await self.session.execute(
            select(func.count(DocumentDB.id)).where(DocumentDB.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_by_property(
        self, user_id: str, property_id: str, limit: int = 50
    ) -> list[DocumentDB]:
        """Get all documents for a property (scoped to user)."""
        result = await self.session.execute(
            select(DocumentDB)
            .where(DocumentDB.user_id == user_id, DocumentDB.property_id == property_id)
            .order_by(DocumentDB.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_expiring_soon(
        self, user_id: str, days_ahead: int = 30, limit: int = 50
    ) -> list[DocumentDB]:
        """Get documents expiring within specified days."""
        now = datetime.now(UTC)
        expiry_threshold = now + timedelta(days=days_ahead)

        result = await self.session.execute(
            select(DocumentDB)
            .where(
                DocumentDB.user_id == user_id,
                DocumentDB.expiry_date.is_not(None),
                DocumentDB.expiry_date >= now,
                DocumentDB.expiry_date <= expiry_threshold,
                DocumentDB.expiry_notified == False,  # noqa: E712
            )
            .order_by(DocumentDB.expiry_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self,
        document: DocumentDB,
        property_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        description: Optional[str] = None,
        expiry_date: Optional[datetime] = None,
        ocr_status: Optional[str] = None,
        extracted_text: Optional[str] = None,
    ) -> DocumentDB:
        """Update document metadata."""
        import json

        if property_id is not None:
            document.property_id = property_id
        if category is not None:
            document.category = category
        if tags is not None:
            document.tags = json.dumps(tags)
        if description is not None:
            document.description = description
        if expiry_date is not None:
            document.expiry_date = expiry_date
        if ocr_status is not None:
            document.ocr_status = ocr_status
        if extracted_text is not None:
            document.extracted_text = extracted_text

        await self.session.flush()
        return document

    async def mark_expiry_notified(self, document: DocumentDB) -> None:
        """Mark document as expiry notification sent."""
        document.expiry_notified = True
        await self.session.flush()

    async def delete(self, document: DocumentDB) -> None:
        """Delete a document record."""
        await self.session.delete(document)
        await self.session.flush()

    async def delete_by_user(self, user_id: str) -> int:
        """Delete all documents for a user (returns count deleted)."""
        result = await self.session.execute(select(DocumentDB).where(DocumentDB.user_id == user_id))
        documents = list(result.scalars().all())
        count = len(documents)
        for doc in documents:
            await self.session.delete(doc)
        await self.session.flush()
        return count

    async def get_pending_ocr(self, limit: int = 100) -> list[DocumentDB]:
        """Get documents pending OCR processing."""
        result = await self.session.execute(
            select(DocumentDB)
            .where(DocumentDB.ocr_status == "pending")
            .order_by(DocumentDB.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_update_ocr_status(self, document_ids: list[str], status: str) -> int:
        """Bulk update OCR status for multiple documents."""
        result = await self.session.execute(
            update(DocumentDB).where(DocumentDB.id.in_(document_ids)).values(ocr_status=status)
        )
        await self.session.flush()
        return result.rowcount


class DocumentTemplateRepository:
    """Repository for DocumentTemplateDB operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        name: str,
        template_type: str,
        content: str,
        description: Optional[str] = None,
        variables: Optional[dict] = None,
        is_default: bool = False,
    ) -> DocumentTemplateDB:
        """Create a new document template."""
        template = DocumentTemplateDB(
            id=str(uuid4()),
            user_id=user_id,
            name=name,
            template_type=template_type,
            content=content,
            description=description,
            variables=variables,
            is_default=is_default,
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def get_by_id(
        self, template_id: str, user_id: Optional[str] = None
    ) -> Optional[DocumentTemplateDB]:
        """Get template by ID, optionally scoped to user."""
        query = select(DocumentTemplateDB).where(DocumentTemplateDB.id == template_id)
        if user_id:
            query = query.where(DocumentTemplateDB.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: str,
        template_type: Optional[str] = None,
        include_defaults: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> list[DocumentTemplateDB]:
        """Get templates for a user with optional filtering."""
        query = select(DocumentTemplateDB).where(DocumentTemplateDB.user_id == user_id)
        if template_type:
            query = query.where(DocumentTemplateDB.template_type == template_type)
        query = query.order_by(DocumentTemplateDB.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: str,
        template_type: Optional[str] = None,
    ) -> int:
        """Count templates for a user."""
        query = (
            select(func.count())
            .select_from(DocumentTemplateDB)
            .where(DocumentTemplateDB.user_id == user_id)
        )
        if template_type:
            query = query.where(DocumentTemplateDB.template_type == template_type)
        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def get_default_template(
        self, template_type: str, user_id: Optional[str] = None
    ) -> Optional[DocumentTemplateDB]:
        """Get the default template for a type."""
        query = select(DocumentTemplateDB).where(
            DocumentTemplateDB.template_type == template_type,
            DocumentTemplateDB.is_default.is_(True),
        )
        if user_id:
            query = query.where(DocumentTemplateDB.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self,
        template: DocumentTemplateDB,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        variables: Optional[dict] = None,
        is_default: Optional[bool] = None,
    ) -> DocumentTemplateDB:
        """Update template fields."""
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if content is not None:
            template.content = content
        if variables is not None:
            template.variables = variables
        if is_default is not None:
            template.is_default = is_default
        await self.session.flush()
        return template

    async def delete(self, template: DocumentTemplateDB) -> None:
        """Delete a template."""
        await self.session.delete(template)
        await self.session.flush()


class SignatureRequestRepository:
    """Repository for SignatureRequestDB operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        title: str,
        provider: str,
        signers: list[dict],
        document_id: Optional[str] = None,
        template_id: Optional[str] = None,
        subject: Optional[str] = None,
        message: Optional[str] = None,
        property_id: Optional[str] = None,
        variables: Optional[dict] = None,
        document_content_hash: Optional[str] = None,
        provider_envelope_id: Optional[str] = None,
        status: str = "draft",
        expires_at: Optional[datetime] = None,
    ) -> SignatureRequestDB:
        """Create a new signature request."""
        request = SignatureRequestDB(
            id=str(uuid4()),
            user_id=user_id,
            title=title,
            subject=subject,
            message=message,
            provider=provider,
            provider_envelope_id=provider_envelope_id,
            document_id=document_id,
            template_id=template_id,
            property_id=property_id,
            document_content_hash=document_content_hash,
            signers=signers,
            variables=variables,
            status=status,
            expires_at=expires_at,
        )
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_by_id(
        self, request_id: str, user_id: Optional[str] = None
    ) -> Optional[SignatureRequestDB]:
        """Get signature request by ID, optionally scoped to user."""
        query = select(SignatureRequestDB).where(SignatureRequestDB.id == request_id)
        if user_id:
            query = query.where(SignatureRequestDB.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_provider_envelope_id(
        self, provider: str, envelope_id: str
    ) -> Optional[SignatureRequestDB]:
        """Get signature request by provider envelope ID."""
        result = await self.session.execute(
            select(SignatureRequestDB).where(
                SignatureRequestDB.provider == provider,
                SignatureRequestDB.provider_envelope_id == envelope_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        property_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[SignatureRequestDB]:
        """Get signature requests for a user with filtering."""
        query = select(SignatureRequestDB).where(SignatureRequestDB.user_id == user_id)
        if status:
            query = query.where(SignatureRequestDB.status == status)
        if property_id:
            query = query.where(SignatureRequestDB.property_id == property_id)
        query = query.order_by(SignatureRequestDB.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> int:
        """Count signature requests for a user."""
        query = (
            select(func.count())
            .select_from(SignatureRequestDB)
            .where(SignatureRequestDB.user_id == user_id)
        )
        if status:
            query = query.where(SignatureRequestDB.status == status)
        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def update_status(
        self,
        request: SignatureRequestDB,
        status: str,
        error_message: Optional[str] = None,
        sent_at: Optional[datetime] = None,
        viewed_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        cancelled_at: Optional[datetime] = None,
    ) -> SignatureRequestDB:
        """Update signature request status."""
        request.status = status
        if error_message is not None:
            request.error_message = error_message
        if sent_at is not None:
            request.sent_at = sent_at
        if viewed_at is not None:
            request.viewed_at = viewed_at
        if completed_at is not None:
            request.completed_at = completed_at
        if cancelled_at is not None:
            request.cancelled_at = cancelled_at
        await self.session.flush()
        return request

    async def update_signers(
        self, request: SignatureRequestDB, signers: list[dict]
    ) -> SignatureRequestDB:
        """Update signer information (e.g., status changes from webhook)."""
        request.signers = signers
        await self.session.flush()
        return request

    async def update_provider_envelope_id(
        self, request: SignatureRequestDB, envelope_id: str
    ) -> SignatureRequestDB:
        """Update provider envelope ID after sending."""
        request.provider_envelope_id = envelope_id
        await self.session.flush()
        return request

    async def mark_reminder_sent(self, request: SignatureRequestDB) -> SignatureRequestDB:
        """Mark that a reminder was sent."""
        request.reminder_sent_at = datetime.now(UTC)
        request.reminder_count += 1
        await self.session.flush()
        return request

    async def get_expiring_requests(self, within_hours: int = 24) -> list[SignatureRequestDB]:
        """Get requests expiring within specified hours that haven't been notified."""
        threshold = datetime.now(UTC) + timedelta(hours=within_hours)
        result = await self.session.execute(
            select(SignatureRequestDB).where(
                SignatureRequestDB.status.in_(["sent", "viewed", "partially_signed"]),
                SignatureRequestDB.expires_at <= threshold,
                SignatureRequestDB.expires_at > datetime.now(UTC),
            )
        )
        return list(result.scalars().all())

    async def cancel(self, request: SignatureRequestDB) -> SignatureRequestDB:
        """Cancel a signature request."""
        request.status = "cancelled"
        request.cancelled_at = datetime.now(UTC)
        await self.session.flush()
        return request

    async def delete(self, request: SignatureRequestDB) -> None:
        """Delete a signature request."""
        await self.session.delete(request)
        await self.session.flush()


class SignedDocumentRepository:
    """Repository for SignedDocumentDB operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        signature_request_id: str,
        storage_path: str,
        file_size: int,
        document_id: Optional[str] = None,
        provider_document_id: Optional[str] = None,
        certificate_url: Optional[str] = None,
        signature_hash: Optional[str] = None,
    ) -> SignedDocumentDB:
        """Create a signed document record."""
        signed_doc = SignedDocumentDB(
            id=str(uuid4()),
            signature_request_id=signature_request_id,
            document_id=document_id,
            storage_path=storage_path,
            file_size=file_size,
            provider_document_id=provider_document_id,
            certificate_url=certificate_url,
            signature_hash=signature_hash,
        )
        self.session.add(signed_doc)
        await self.session.flush()
        return signed_doc

    async def get_by_id(self, signed_doc_id: str) -> Optional[SignedDocumentDB]:
        """Get signed document by ID."""
        result = await self.session.execute(
            select(SignedDocumentDB).where(SignedDocumentDB.id == signed_doc_id)
        )
        return result.scalar_one_or_none()

    async def get_by_signature_request(
        self, signature_request_id: str
    ) -> Optional[SignedDocumentDB]:
        """Get signed document by signature request ID."""
        result = await self.session.execute(
            select(SignedDocumentDB).where(
                SignedDocumentDB.signature_request_id == signature_request_id
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, signed_doc: SignedDocumentDB) -> None:
        """Delete a signed document record."""
        await self.session.delete(signed_doc)
        await self.session.flush()
