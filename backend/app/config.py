import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Sri Lakshmi Snacks ERP"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "sri_lakshmi_snacks_tiruchirappalli_super_secret_jwt_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 12 hours for factory shift convenience

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

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()
