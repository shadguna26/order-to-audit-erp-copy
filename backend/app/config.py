import os
from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Sri Lakshmi Snacks ERP"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "sri_lakshmi_snacks_tiruchirappalli_super_secret_jwt_key_2026"
    OTP_SECRET: str = "sri_lakshmi_snacks_otp_hmac_secret_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # OTP & SMS Auth settings
    DEMO_MODE: bool = True
    SMS_PROVIDER: str = "console"  # console | msg91 | twilio
    MSG91_AUTH_KEY: Optional[str] = None
    MSG91_TEMPLATE_ID: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 30
    OTP_HOURLY_LIMIT_PER_MOBILE: int = 5
    OTP_HOURLY_LIMIT_PER_IP: int = 20

    DATABASE_URL: str = "sqlite:///./snack_erp.db"

    # Sri Lakshmi Snacks Company Profile (Tamil Nadu)
    COMPANY_NAME: str = "Sri Lakshmi Snacks"
    COMPANY_ADDRESS: str = "Plot No. 14, Thuvakudi Industrial Estate, Tiruchirappalli, Tamil Nadu - 620015"
    COMPANY_STATE: str = "Tamil Nadu"
    COMPANY_STATE_CODE: str = "33"
    COMPANY_GSTIN: str = "33AABCS1234F1Z8"
    COMPANY_PHONE: str = "+91 94431 23456"
    COMPANY_EMAIL: str = "orders@srilakshmisnacks.in"

    # Default tolerance for production yield / raw material variances
    DEFAULT_VARIANCE_TOLERANCE_PCT: float = 3.0

    @model_validator(mode="after")
    def validate_production_demo_mode(self):
        if self.ENVIRONMENT.strip().lower() == "production" and self.DEMO_MODE:
            raise ValueError("Refusing to start: DEMO_MODE=true is forbidden when ENVIRONMENT=production")
        return self

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()
