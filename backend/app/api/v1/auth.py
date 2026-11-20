from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User, UserRole
from app.schemas.auth import Token, UserCreate, UserRegister, ForgotPasswordRequest, UserResponse
from app.services.auth_service import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "username": user.username
    }

@router.post("/register", response_model=Token)
def register_user(
    data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new staff member (salesman, production, accountant, or admin).
    """
    clean_username = data.username.strip().lower()
    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{clean_username}' is already registered."
        )

    new_user = User(
        username=clean_username,
        full_name=data.full_name.strip(),
        hashed_password=get_password_hash(data.password),
        role=data.role,
        phone=data.phone.strip() if data.phone else None,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.username, "role": new_user.role.value})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": new_user.role,
        "full_name": new_user.full_name,
        "username": new_user.username
    }

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Password reset verification and update for existing staff members.
    """
    clean_username = data.username.strip().lower()
    user = db.query(User).filter(User.username == clean_username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User account '{clean_username}' not found."
        )

    if len(data.new_password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 4 characters long."
        )

    user.hashed_password = get_password_hash(data.new_password)
    db.commit()

    return {
        "status": "success",
        "message": f"Password for {user.full_name} ({user.username}) updated successfully. You can now log in."
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER]))
):
    """Only Admin and Owner can view full user roster."""
    return db.query(User).order_by(User.id).all()
