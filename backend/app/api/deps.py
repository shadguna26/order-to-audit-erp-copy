from typing import Generator, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.auth import User, UserRole
from app.models.business import Business
from app.schemas.auth import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/otp/verify")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_raw = payload.get("user_id") or payload.get("sub")
        role: str = payload.get("role")
        biz_id_raw = payload.get("business_id")
        token_type: str = payload.get("type")
        if user_id_raw is None or role is None or token_type != "access":
            raise credentials_exception
        token_data = TokenData(
            user_id=int(user_id_raw),
            role=UserRole(role),
            business_id=int(biz_id_raw) if biz_id_raw is not None else None,
        )
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    if token_data.business_id is not None and user.business_id != token_data.business_id:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return user


def get_current_business(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Business:
    """Resolve the active business for the authenticated user from the JWT/user record."""
    biz = db.query(Business).filter(Business.id == current_user.business_id).first()
    if not biz or not biz.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business account is inactive or not found",
        )
    return biz

def require_roles(allowed_roles: List[UserRole]):
    """
    NON-NEGOTIABLE RULE 5:
    Role-based access: salesman, admin, production, accountant (read-only), owner.
    Enforce on the backend, not just by hiding screens.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker
