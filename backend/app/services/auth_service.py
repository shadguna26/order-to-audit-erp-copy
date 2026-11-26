from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from app.config import settings
from app.models.auth import UserRole


def create_access_token(
    user_id: int,
    role: UserRole,
    business_id: int = 1,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a 15-minute access JWT containing user_id, role, and business_id."""
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role.value if isinstance(role, UserRole) else str(role),
        "business_id": business_id,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
