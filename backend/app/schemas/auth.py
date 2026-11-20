from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.auth import UserRole

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    full_name: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    role: UserRole = UserRole.SALESMAN
    phone: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    username: str
    new_password: str
    phone: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
