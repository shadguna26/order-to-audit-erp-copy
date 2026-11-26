from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.models.auth import UserRole


class OTPRequestIn(BaseModel):
    mobile: str


class OTPRequestOut(BaseModel):
    message: str
    cooldown_seconds: int = 30
    demo_code: Optional[str] = None


class OTPVerifyIn(BaseModel):
    mobile: str
    otp: str = Field(..., min_length=6, max_length=6)
    device_label: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    mobile: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: UserRole
    full_name: str
    mobile: str
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


class UserCreateIn(BaseModel):
    mobile: str
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.SALESMAN


class UserUpdateIn(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
