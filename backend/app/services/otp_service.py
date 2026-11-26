import hmac
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth import UserRole, OTPRequest, RefreshToken
from app.services.audit_service import log_audit_event

_MOBILE_RE = re.compile(r"^\+91[6-9]\d{9}$")


def normalize_mobile(raw_mobile: str) -> str:
    """
    Normalize Indian mobile numbers into +91XXXXXXXXXX format.
    Accepts 10-digit (9876543210), 0-prefixed (09876543210),
    91-prefixed (919876543210), or +91-prefixed (+91 98765-43210).
    """
    if not raw_mobile or not isinstance(raw_mobile, str):
        raise ValueError("Mobile number is required")

    cleaned = re.sub(r"[\s\-().]", "", raw_mobile.strip())

    if cleaned.startswith("+91"):
        normalized = cleaned
    elif cleaned.startswith("91") and len(cleaned) == 12:
        normalized = f"+{cleaned}"
    elif cleaned.startswith("0") and len(cleaned) == 11:
        normalized = f"+91{cleaned[1:]}"
    elif len(cleaned) == 10 and cleaned.isdigit():
        normalized = f"+91{cleaned}"
    else:
        raise ValueError("Enter a valid 10-digit Indian mobile number")

    if not _MOBILE_RE.match(normalized):
        raise ValueError("Enter a valid 10-digit Indian mobile number")

    return normalized


def mask_mobile(mobile: str) -> str:
    """Mask middle digits of a normalized mobile number for audit logs."""
    if not mobile:
        return "unknown"
    if len(mobile) >= 4:
        return f"+91XXXXXX{mobile[-4:]}"
    return "******"


def generate_otp_code() -> str:
    """Generate a cryptographically random 6-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(mobile: str, code: str) -> str:
    """Compute HMAC-SHA256 digest of mobile + OTP using server secret."""
    msg = f"{mobile}:{code}".encode("utf-8")
    key = settings.OTP_SECRET.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_otp_hash(mobile: str, code: str, expected_hash: str) -> bool:
    """Constant-time comparison of candidate OTP against stored HMAC-SHA256 hash."""
    if not code or not expected_hash:
        return False
    candidate_hash = hash_otp(mobile, code)
    return hmac.compare_digest(candidate_hash, expected_hash)


def generate_refresh_token() -> str:
    """Generate a cryptographically random opaque refresh token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    """Hash a refresh token with HMAC-SHA256 before database storage."""
    key = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(key, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()


def get_refresh_ttl_for_role(role: UserRole) -> timedelta:
    """Session length by role: salesman 30d, owner 7d, admin/accountant/production 12h."""
    if role == UserRole.SALESMAN:
        return timedelta(days=30)
    if role == UserRole.OWNER:
        return timedelta(days=7)
    return timedelta(hours=12)


def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> int:
    """Revoke all active refresh tokens for a user immediately."""
    now = datetime.now(timezone.utc)
    active_tokens = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .all()
    )
    for tok in active_tokens:
        tok.revoked_at = now
    db.flush()
    return len(active_tokens)


def log_auth_event(
    db: Session,
    action: str,
    mobile: str,
    ip: Optional[str],
    user_agent: Optional[str],
    user_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Write auth event (otp_requested, login_success, login_failed, lockout, logout) to audit_log."""
    payload: Dict[str, Any] = {
        "mobile": mask_mobile(mobile),
        "ip": ip or "unknown",
        "user_agent": (user_agent or "unknown")[:255],
        "time": datetime.now(timezone.utc).isoformat(),
    }
    if details:
        payload.update(details)

    log_audit_event(
        db=db,
        user_id=user_id,
        table_name="auth",
        record_id=user_id or 0,
        action=action,
        old_values=None,
        new_values=payload,
    )
