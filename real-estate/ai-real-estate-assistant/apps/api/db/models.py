"""SQLAlchemy models for user authentication."""

from datetime import UTC, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Account lockout fields (Task #47: Auth Security Hardening)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        "OAuthAccount", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked due to failed login attempts."""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until


class RefreshToken(Base):
    """Refresh token model for JWT token rotation."""

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_revoked(self) -> bool:
        """Check if token is revoked."""
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(UTC) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"


class OAuthAccount(Base):
    """OAuth account model for social login."""

    __tablename__ = "oauth_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # google, apple
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    # Composite unique index for provider + provider_user_id
    __table_args__ = (
        Index("ix_oauth_accounts_provider_user", "provider", "provider_user_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<OAuthAccount(id={self.id}, provider={self.provider})>"


class PasswordResetToken(Base):
    """Password reset token model."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        from datetime import UTC, datetime

        return datetime.now(UTC) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.is_used and not self.is_expired

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"


class EmailVerificationToken(Base):
    """Email verification token model."""

    __tablename__ = "email_verification_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        from datetime import UTC, datetime

        return datetime.now(UTC) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.is_used and not self.is_expired

    def __repr__(self) -> str:
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id})>"


class SavedSearchDB(Base):
    """Database model for user saved searches."""

    __tablename__ = "saved_searches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Search criteria (stored as JSON)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Alert settings
    alert_frequency: Mapped[str] = mapped_column(
        String(20), default="daily", nullable=False
    )  # instant, daily, weekly, none
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_new: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_price_drop: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="saved_searches")

    def __repr__(self) -> str:
        return f"<SavedSearchDB(id={self.id}, user_id={self.user_id}, name={self.name})>"


class CollectionDB(Base):
    """Database model for user property collections (folders for favorites)."""

    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="collections")
    favorites: Mapped[list["FavoriteDB"]] = relationship(
        "FavoriteDB", back_populates="collection", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_collections_user_default", "user_id", "is_default"),)

    def __repr__(self) -> str:
        return f"<CollectionDB(id={self.id}, user_id={self.user_id}, name={self.name})>"


class FavoriteDB(Base):
    """Database model for user property favorites."""

    __tablename__ = "favorites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(
        String(255),  # String to match ChromaDB document IDs
        nullable=False,
        index=True,
    )
    collection_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("collections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="favorites")
    collection: Mapped[Optional["CollectionDB"]] = relationship(
        "CollectionDB", back_populates="favorites"
    )

    # Unique constraint: one user can favorite a property once
    __table_args__ = (Index("uq_favorites_user_property", "user_id", "property_id", unique=True),)

    def __repr__(self) -> str:
        return f"<FavoriteDB(id={self.id}, user_id={self.user_id}, property_id={self.property_id})>"


class PriceSnapshot(Base):
    """Database model for property price snapshots (price history tracking)."""

    __tablename__ = "price_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    property_id: Mapped[str] = mapped_column(
        String(255),  # String to match ChromaDB document IDs
        nullable=False,
        index=True,
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # ingestion source
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Composite index for efficient queries
    __table_args__ = (Index("ix_price_snapshots_property_recorded", "property_id", "recorded_at"),)

    def __repr__(self) -> str:
        return f"<PriceSnapshot(property_id={self.property_id}, price={self.price}, recorded_at={self.recorded_at})>"


class MarketAnomaly(Base):
    """Database model for detected market anomalies."""

    __tablename__ = "market_anomalies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Anomaly classification
    anomaly_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # price_spike, price_drop, volume_spike, volume_drop
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical

    # Scope (what entity has the anomaly)
    scope_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # property, city, district, market
    scope_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # property_id, city name, district name

    # Detection details
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)  # z_score, iqr, seasonal
    threshold_used: Mapped[float] = mapped_column(Float, nullable=False)

    # Anomaly data
    metric_name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # price, price_per_sqm, volume
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    deviation_percent: Mapped[float] = mapped_column(Float, nullable=False)
    z_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Time periods for comparison
    baseline_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    baseline_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    comparison_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    comparison_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Alert tracking
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dismissed_by: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )  # user_id who dismissed
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Additional context (property details, related anomalies, etc.)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_anomalies_scope_detected", "scope_type", "scope_id", "detected_at"),
        Index("ix_anomalies_severity", "severity"),
        Index("ix_anomalies_type", "anomaly_type"),
    )

    def __repr__(self) -> str:
        return f"<MarketAnomaly(id={self.id}, type={self.anomaly_type}, severity={self.severity}, scope={self.scope_type}:{self.scope_id})>"


# =============================================================================
# Lead Scoring System Models (Task #55)
# =============================================================================


class Lead(Base):
    """Lead model for tracking all visitors (anonymous + registered).

    A lead represents a potential buyer/renter who has interacted with the platform.
    Can be anonymous (tracked via cookie) or registered user.
    """

    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Visitor identification (cookie-based for anonymous users)
    visitor_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )  # Cookie UUID
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Contact information (optional, captured via forms)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Budget preferences
    budget_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    budget_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    preferred_locations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Lead status
    status: Mapped[str] = mapped_column(
        String(50), default="new", nullable=False
    )  # new, contacted, qualified, converted, lost
    source: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # organic, referral, ads, direct

    # Current score (denormalized for quick access)
    current_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # GDPR compliance
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", backref="leads")
    interactions: Mapped[list["LeadInteraction"]] = relationship(
        "LeadInteraction", back_populates="lead", cascade="all, delete-orphan"
    )
    scores: Mapped[list["LeadScore"]] = relationship(
        "LeadScore", back_populates="lead", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["AgentAssignment"]] = relationship(
        "AgentAssignment", back_populates="lead", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_leads_status", "status"),
        Index("ix_leads_score", "current_score"),
        Index("ix_leads_last_activity", "last_activity_at"),
    )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, visitor_id={self.visitor_id[:8]}..., score={self.current_score}, status={self.status})>"


class LeadInteraction(Base):
    """Lead interaction model for tracking all visitor behaviors.

    Records every interaction a lead has with the platform:
    - Searches performed
    - Properties viewed
    - Favorites added
    - Inquiries submitted
    - Contact requests
    """

    __tablename__ = "lead_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    lead_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Interaction type and details
    interaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # search, view, favorite, inquiry, contact, schedule_viewing
    property_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    search_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional context (filters used, form data, etc.)
    interaction_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Session information
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    page_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Time spent (for view interactions, in seconds)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="interactions")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_interactions_lead_type", "lead_id", "interaction_type"),
        Index("ix_interactions_lead_created", "lead_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<LeadInteraction(id={self.id}, lead_id={self.lead_id[:8]}..., type={self.interaction_type})>"


class LeadScore(Base):
    """Lead score model for tracking score history and breakdowns.

    Stores calculated scores with full explainability:
    - Total score (0-100)
    - Component scores (search activity, engagement, intent)
    - Factors that contributed to the score
    - AI-generated recommendations
    """

    __tablename__ = "lead_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    lead_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Total composite score (0-100)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Component scores (0-100 each)
    search_activity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_score: Mapped[int] = mapped_column(Integer, nullable=False)
    intent_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Detailed breakdown for explainability
    score_factors: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )  # {"search_count": 15, "favorites": 3, "views": 42, ...}

    # AI-generated insights and recommendations
    recommendations: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # ["High interest in Berlin apartments", ...]

    # Model version for tracking scoring algorithm changes
    model_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    # Timestamp
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="scores")

    # Indexes
    __table_args__ = (Index("ix_scores_lead_calculated", "lead_id", "calculated_at"),)

    def __repr__(self) -> str:
        return f"<LeadScore(id={self.id}, lead_id={self.lead_id[:8]}..., total={self.total_score})>"


class AgentAssignment(Base):
    """Agent assignment model for assigning leads to agents.

    Supports:
    - Multiple agents per lead (team approach)
    - Primary agent designation
    - Assignment history tracking
    """

    __tablename__ = "agent_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    lead_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Assignment details
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    assigned_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Status tracking
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    unassigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    unassigned_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="assignments")
    agent: Mapped["User"] = relationship("User", foreign_keys=[agent_id], backref="assigned_leads")
    assigner: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_by], backref="assigned_by_me"
    )

    # Ensure one primary agent per lead
    __table_args__ = (
        Index("uq_assignments_lead_primary", "lead_id", "is_active", "is_primary", unique=False),
        Index("ix_assignments_agent_active", "agent_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<AgentAssignment(lead_id={self.lead_id[:8]}..., agent_id={self.agent_id[:8]}..., primary={self.is_primary})>"


# =============================================================================
# Agent Performance Analytics Models (Task #56)
# =============================================================================


class Deal(Base):
    """Deal model for tracking closed transactions.

    Created when a lead's status changes to 'converted'.
    Tracks the full deal lifecycle from offer to closing.
    """

    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Lead reference
    lead_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Property reference (nullable - may be off-platform deal)
    property_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Agent reference
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True
    )

    # Deal details
    deal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # sale, rent
    property_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    property_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    property_district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Financial
    deal_value: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")

    # Deal stages
    status: Mapped[str] = mapped_column(
        String(20), default="offer_submitted", nullable=False
    )  # offer_submitted, offer_accepted, contract_signed, closed, fell_through

    # Timestamps for time tracking
    offer_submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    offer_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    contract_signed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", backref="deals")
    agent: Mapped[Optional["User"]] = relationship("User", backref="deals")
    commissions: Mapped[list["Commission"]] = relationship(
        "Commission", back_populates="deal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_deals_agent_status", "agent_id", "status"),
        Index("ix_deals_closed_at", "closed_at"),
    )

    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, agent_id={self.agent_id[:8] if self.agent_id else 'None'}..., value={self.deal_value}, status={self.status})>"


class Commission(Base):
    """Commission model for tracking agent earnings.

    Supports split commissions and tiered rates.
    """

    __tablename__ = "commissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # References
    deal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True
    )

    # Commission details
    commission_type: Mapped[str] = mapped_column(
        String(20), default="primary"
    )  # primary, split, referral
    commission_rate: Mapped[float] = mapped_column(Float, nullable=False)  # e.g., 0.03 for 3%
    commission_amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, approved, paid, clawed_back

    # Payment tracking
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", back_populates="commissions")
    agent: Mapped[Optional["User"]] = relationship("User", backref="commissions")

    def __repr__(self) -> str:
        return f"<Commission(id={self.id}, deal_id={self.deal_id[:8]}..., amount={self.commission_amount}, status={self.status})>"


class AgentGoal(Base):
    """Agent goal model for tracking performance targets.

    Supports multiple goal types (leads, deals, revenue).
    """

    __tablename__ = "agent_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Goal details
    goal_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # leads, deals, revenue, gci (gross commission income)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, default=0)

    # Period
    period_type: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # daily, weekly, monthly, quarterly, yearly
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    achieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    agent: Mapped[Optional["User"]] = relationship("User", backref="goals")

    __table_args__ = (
        Index("ix_agent_goals_agent_active", "agent_id", "is_active"),
        Index("ix_agent_goals_period", "period_start", "period_end"),
    )

    def __repr__(self) -> str:
        return f"<AgentGoal(id={self.id}, agent_id={self.agent_id[:8]}..., type={self.goal_type}, target={self.target_value})>"


# =============================================================================
# Push Notification System Models (Task #63)
# =============================================================================


class PushSubscription(Base):
    """Web Push subscription for browser notifications.

    Stores browser push subscription data for sending web push notifications
    to users about price drops, new properties, and market anomalies.
    """

    __tablename__ = "push_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Push subscription data (from browser PushSubscription JSON)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)  # VAPID p256dh key
    auth: Mapped[str] = mapped_column(String(255), nullable=False)  # VAPID auth secret

    # Device metadata
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    device_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # "Chrome on Windows", etc.

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="push_subscriptions")

    # Indexes
    __table_args__ = (Index("ix_push_user_active", "user_id", "is_active"),)

    def __repr__(self) -> str:
        return f"<PushSubscription(id={self.id[:8]}..., user_id={self.user_id[:8]}..., active={self.is_active})>"


# =============================================================================
# Agent/Broker System Models (Task #45)
# =============================================================================


class AgentProfile(Base):
    """Agent/broker professional profile linked to User.

    Stores professional information for real estate agents including
    agency details, specializations, ratings, and contact information.
    """

    __tablename__ = "agent_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Professional Information
    agency_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    agency_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )  # For multi-tenancy
    license_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    license_state: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # For regional licensing

    # Contact (professional, can differ from User.email)
    professional_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    professional_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    office_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Specialization
    specialties: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # ["residential", "commercial", "luxury"]
    service_areas: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # ["Berlin", "Munich"]
    property_types: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # ["apartment", "house", "investment"]
    languages: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["en", "de", "pl"]

    # Rating & Reviews
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Track record
    total_rentals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    verification_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Media
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="agent_profile")
    listings: Mapped[list["AgentListing"]] = relationship(
        "AgentListing", back_populates="agent", cascade="all, delete-orphan"
    )
    inquiries: Mapped[list["AgentInquiry"]] = relationship(
        "AgentInquiry", back_populates="agent", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_agent_profiles_agency", "agency_id"),
        Index("ix_agent_profiles_rating", "average_rating"),
    )

    def __repr__(self) -> str:
        return f"<AgentProfile(id={self.id[:8]}..., user_id={self.user_id[:8]}..., agency={self.agency_name})>"


class AgentListing(Base):
    """Links agents to properties they represent.

    An agent can have multiple listings, and a property can have
    multiple agents (co-listing). Supports both sale and rental listings.
    """

    __tablename__ = "agent_listings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agent_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,  # ChromaDB property ID
    )
    listing_type: Mapped[str] = mapped_column(
        String(20), default="sale", nullable=False
    )  # sale, rent, both
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Primary agent for property
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    commission_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Optional override
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    agent: Mapped["AgentProfile"] = relationship("AgentProfile", back_populates="listings")

    __table_args__ = (Index("uq_agent_listing", "agent_id", "property_id", unique=True),)

    def __repr__(self) -> str:
        return f"<AgentListing(agent_id={self.agent_id[:8]}..., property_id={self.property_id[:8]}..., type={self.listing_type})>"


class AgentInquiry(Base):
    """Contact inquiries sent to agents.

    Stores all contact form submissions from users/visitors to agents.
    Can be linked to a specific property or be general inquiries.
    """

    __tablename__ = "agent_inquiries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agent_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Inquirer info (can be anonymous or registered)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    visitor_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )  # For anonymous
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Inquiry details
    property_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    inquiry_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # general, property, financing
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="new", nullable=False
    )  # new, read, responded, closed

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent: Mapped["AgentProfile"] = relationship("AgentProfile", back_populates="inquiries")
    user: Mapped[Optional["User"]] = relationship("User", backref="agent_inquiries")

    __table_args__ = (
        Index("ix_inquiries_status", "status"),
        Index("ix_inquiries_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AgentInquiry(id={self.id[:8]}..., agent_id={self.agent_id[:8]}..., type={self.inquiry_type}, status={self.status})>"


class ViewingAppointment(Base):
    """Scheduled property viewings with agents.

    Manages viewing appointment requests, confirmations, and cancellations.
    Supports both registered users and anonymous visitors.
    """

    __tablename__ = "viewing_appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agent_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Client info
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    visitor_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Property
    property_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Scheduling
    proposed_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="requested", nullable=False
    )  # requested, confirmed, cancelled, completed
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    agent: Mapped["AgentProfile"] = relationship("AgentProfile", backref="viewing_appointments")
    user: Mapped[Optional["User"]] = relationship("User", backref="viewing_appointments")

    __table_args__ = (
        Index("ix_appointments_datetime", "proposed_datetime"),
        Index("ix_appointments_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ViewingAppointment(id={self.id[:8]}..., agent_id={self.agent_id[:8]}..., status={self.status})>"


# =============================================================================
# Document Management System Models (Task #43)
# =============================================================================


class DocumentDB(Base):
    """Document model for user property-related documents.

    Stores metadata for uploaded documents including contracts,
    inspection reports, photos, and other property-related files.
    Supports OCR text extraction for searchability.
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # User reference (required)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Property reference (optional - document may not be linked to a specific property)
    property_id: Mapped[Optional[str]] = mapped_column(
        String(255),  # String to match ChromaDB document IDs
        nullable=True,
        index=True,
    )

    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # Unique stored filename
    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Original upload name
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # MIME type
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Size in bytes
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)  # Path to stored file

    # Document metadata
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # contract, inspection, photo, financial, other
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of tags
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # OCR fields
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # OCR extracted text
    ocr_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, processing, completed, failed

    # Expiry tracking
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="documents")

    # Indexes
    __table_args__ = (
        Index("ix_documents_category", "category"),
        Index("ix_documents_ocr_status", "ocr_status"),
        Index("ix_documents_expiry", "expiry_date"),
    )

    def __repr__(self) -> str:
        return f"<DocumentDB(id={self.id[:8]}..., user_id={self.user_id[:8]}..., filename={self.original_filename[:20]}...)>"


class DocumentTemplateDB(Base):
    """Document templates with Jinja2 placeholders for e-signature.

    Stores reusable document templates (rental agreements, purchase offers, etc.)
    that can be rendered with variable substitution.
    """

    __tablename__ = "document_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Template info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # rental_agreement, purchase_offer, lease_renewal, custom

    # Template content (Jinja2 HTML)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Variable definitions (JSON schema for validation)
    variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Default template flag
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="document_templates")

    # Indexes
    __table_args__ = (
        Index("ix_document_templates_type", "template_type"),
        Index("ix_document_templates_user_type", "user_id", "template_type"),
    )

    def __repr__(self) -> str:
        return f"<DocumentTemplateDB(id={self.id[:8]}..., name={self.name[:30]}, type={self.template_type})>"


class SignatureRequestDB(Base):
    """E-signature request tracking.

    Tracks signature requests sent via external providers (HelloSign, DocuSign).
    Stores signer information, status, and provider integration details.
    """

    __tablename__ = "signature_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source document/template
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True
    )

    # Provider info
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # hellosign, docusign
    provider_envelope_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Document details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    property_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Rendered document metadata
    document_content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # SHA-256

    # Signers (JSON array: [{email, name, role, order, status, signed_at}])
    signers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Template variables used
    variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), default="draft", nullable=False
    )  # draft, sent, viewed, partially_signed, completed, expired, cancelled, declined
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Reminder tracking
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="signature_requests")
    document: Mapped[Optional["DocumentDB"]] = relationship(
        "DocumentDB", backref="signature_requests"
    )
    template: Mapped[Optional["DocumentTemplateDB"]] = relationship(
        "DocumentTemplateDB", backref="signature_requests"
    )
    signed_document: Mapped[Optional["SignedDocumentDB"]] = relationship(
        "SignedDocumentDB", backref="signature_request", uselist=False
    )

    # Indexes
    __table_args__ = (
        Index("ix_signature_requests_status", "status"),
        Index("ix_signature_requests_provider", "provider", "provider_envelope_id"),
        Index("ix_signature_requests_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<SignatureRequestDB(id={self.id[:8]}..., title={self.title[:30]}, status={self.status})>"


class SignedDocumentDB(Base):
    """Final signed documents storage.

    Stores the completed, signed document with verification metadata.
    """

    __tablename__ = "signed_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    signature_request_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("signature_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    # Storage
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Provider metadata
    provider_document_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Verification
    signature_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # Hash for integrity

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    document: Mapped[Optional["DocumentDB"]] = relationship(
        "DocumentDB", backref="signed_documents"
    )

    def __repr__(self) -> str:
        return f"<SignedDocumentDB(id={self.id[:8]}..., request_id={self.signature_request_id[:8]}...)>"
