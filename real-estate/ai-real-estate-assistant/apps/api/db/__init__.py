"""Database layer for user authentication."""

from db.database import get_db, init_db
from db.models import (
    MarketAnomaly,
    OAuthAccount,
    PriceSnapshot,
    PushSubscription,
    RefreshToken,
    User,
)
from db.repositories import (
    AnomalyRepository,
    OAuthAccountRepository,
    PriceSnapshotRepository,
    PushSubscriptionRepository,
    RefreshTokenRepository,
    UserRepository,
)
from db.schemas import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Database
    "get_db",
    "init_db",
    # Models
    "User",
    "RefreshToken",
    "OAuthAccount",
    "PriceSnapshot",
    "MarketAnomaly",
    "PushSubscription",
    # Repositories
    "UserRepository",
    "RefreshTokenRepository",
    "OAuthAccountRepository",
    "PriceSnapshotRepository",
    "AnomalyRepository",
    "PushSubscriptionRepository",
    # Schemas
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
]
