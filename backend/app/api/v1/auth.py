from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.auth import User, UserRole, OTPRequest, RefreshToken
from app.schemas.auth import (
    OTPRequestIn,
    OTPRequestOut,
    OTPVerifyIn,
    TokenOut,
    UserCreateIn,
    UserUpdateIn,
    UserResponse,
)
from app.services.auth_service import create_access_token
from app.services.otp_service import (
    normalize_mobile,
    generate_otp_code,
    hash_otp,
    verify_otp_hash,
    generate_refresh_token,
    hash_refresh_token,
    get_refresh_ttl_for_role,
    revoke_all_user_refresh_tokens,
    log_auth_event,
)
from app.services.sms_service import get_sms_provider
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "unknown")


def _set_refresh_cookie(response: Response, raw_token: str, ttl: timedelta) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=(settings.ENVIRONMENT.strip().lower() == "production"),
        max_age=int(ttl.total_seconds()),
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        samesite="lax",
    )


@router.post("/otp/request", response_model=OTPRequestOut)
def request_otp(
    data: OTPRequestIn,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Request a 6-digit SMS OTP for a +91XXXXXXXXXX mobile number.
    Returns the exact same response shape and errors for registered and unregistered numbers.
    """
    try:
        mobile = normalize_mobile(data.mobile)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    ip = _client_ip(request)
    ua = _user_agent(request)

    # 1. Per-IP hourly limit
    ip_count = (
        db.query(OTPRequest)
        .filter(OTPRequest.ip_address == ip, OTPRequest.created_at >= one_hour_ago)
        .count()
    )
    if ip_count >= settings.OTP_HOURLY_LIMIT_PER_IP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests from this network. Please try again later.",
        )

    # 2. 30-second resend cooldown per mobile
    latest_otp = (
        db.query(OTPRequest)
        .filter(OTPRequest.mobile == mobile)
        .order_by(OTPRequest.created_at.desc(), OTPRequest.id.desc())
        .first()
    )
    if latest_otp:
        elapsed = (now - _as_utc(latest_otp.created_at)).total_seconds()
        if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {settings.OTP_RESEND_COOLDOWN_SECONDS} seconds before requesting another OTP.",
            )

    # 3. Hourly limit per mobile (max 5 sends per hour)
    mobile_count = (
        db.query(OTPRequest)
        .filter(OTPRequest.mobile == mobile, OTPRequest.created_at >= one_hour_ago)
        .count()
    )
    if mobile_count >= settings.OTP_HOURLY_LIMIT_PER_MOBILE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Hourly OTP limit reached for this mobile number. Please try again later.",
        )

    # Invalidate prior unused OTPs for this mobile
    prior_unused = (
        db.query(OTPRequest)
        .filter(OTPRequest.mobile == mobile, OTPRequest.used_at.is_(None))
        .all()
    )
    for row in prior_unused:
        row.used_at = now

    code = generate_otp_code()
    otp_record = OTPRequest(
        mobile=mobile,
        otp_hash=hash_otp(mobile, code),
        expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        attempts=0,
        ip_address=ip,
    )
    db.add(otp_record)

    user = db.query(User).filter(User.mobile == mobile).first()
    log_auth_event(
        db=db,
        action="otp_requested",
        mobile=mobile,
        ip=ip,
        user_agent=ua,
        user_id=user.id if user else None,
    )
    db.commit()

    # Only dispatch SMS if user exists and is active (never leak registration status in response)
    if user and user.is_active:
        get_sms_provider().send_otp(mobile, code)

    return OTPRequestOut(
        message="If this mobile number is registered, an OTP has been sent.",
        cooldown_seconds=settings.OTP_RESEND_COOLDOWN_SECONDS,
        demo_code=code if settings.DEMO_MODE else None,
    )


@router.post("/otp/verify", response_model=TokenOut)
def verify_otp(
    data: OTPVerifyIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Verify 6-digit OTP, issue 15-minute access JWT, and set rotating httpOnly refresh cookie.
    """
    try:
        mobile = normalize_mobile(data.mobile)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    now = datetime.now(timezone.utc)
    ip = _client_ip(request)
    ua = _user_agent(request)
    user = db.query(User).filter(User.mobile == mobile).first()

    otp_req = (
        db.query(OTPRequest)
        .filter(OTPRequest.mobile == mobile, OTPRequest.used_at.is_(None))
        .order_by(OTPRequest.created_at.desc(), OTPRequest.id.desc())
        .first()
    )

    if not otp_req or _as_utc(otp_req.expires_at) < now:
        log_auth_event(
            db=db,
            action="login_failed",
            mobile=mobile,
            ip=ip,
            user_agent=ua,
            user_id=user.id if user else None,
            details={"reason": "missing_or_expired_otp"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    if otp_req.attempts >= settings.OTP_MAX_ATTEMPTS:
        log_auth_event(
            db=db,
            action="lockout",
            mobile=mobile,
            ip=ip,
            user_agent=ua,
            user_id=user.id if user else None,
            details={"reason": "max_attempts_exceeded"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many wrong attempts. Please request a new OTP.",
        )

    if not verify_otp_hash(mobile, data.otp.strip(), otp_req.otp_hash):
        otp_req.attempts += 1
        if otp_req.attempts >= settings.OTP_MAX_ATTEMPTS:
            otp_req.used_at = now
            log_auth_event(
                db=db,
                action="lockout",
                mobile=mobile,
                ip=ip,
                user_agent=ua,
                user_id=user.id if user else None,
                details={"attempts": otp_req.attempts},
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many wrong attempts. Please request a new OTP.",
            )

        log_auth_event(
            db=db,
            action="login_failed",
            mobile=mobile,
            ip=ip,
            user_agent=ua,
            user_id=user.id if user else None,
            details={"attempts": otp_req.attempts},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    # Single use: mark OTP consumed
    otp_req.used_at = now

    if not user or not user.is_active:
        log_auth_event(
            db=db,
            action="login_failed",
            mobile=mobile,
            ip=ip,
            user_agent=ua,
            user_id=user.id if user else None,
            details={"reason": "unknown_or_inactive_user"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    ttl = get_refresh_ttl_for_role(user.role)
    raw_refresh = generate_refresh_token()
    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        device_label=(data.device_label or ua)[:255],
        expires_at=now + ttl,
    )
    db.add(refresh_row)

    log_auth_event(
        db=db,
        action="login_success",
        mobile=mobile,
        ip=ip,
        user_agent=ua,
        user_id=user.id,
        details={"role": user.role.value},
    )
    db.commit()

    access_token = create_access_token(user_id=user.id, role=user.role)
    _set_refresh_cookie(response, raw_refresh, ttl)

    return TokenOut(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role,
        full_name=user.full_name,
        mobile=user.mobile,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenOut)
def refresh_session(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Rotate the httpOnly refresh token and issue a fresh 15-minute access JWT.
    Reuse of a previously rotated/revoked refresh token revokes all tokens for that user.
    """
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    now = datetime.now(timezone.utc)
    ip = _client_ip(request)
    ua = _user_agent(request)
    token_hash = hash_refresh_token(raw_token)

    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not rt:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(User.id == rt.user_id).first()

    # Reuse detection: revoked token presented again -> revoke all user tokens
    if rt.revoked_at is not None:
        revoke_all_user_refresh_tokens(db, rt.user_id)
        log_auth_event(
            db=db,
            action="login_failed",
            mobile=user.mobile if user else "unknown",
            ip=ip,
            user_agent=ua,
            user_id=rt.user_id,
            details={"reason": "refresh_token_reuse"},
        )
        db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. Please log in again.",
        )

    if _as_utc(rt.expires_at) < now:
        rt.revoked_at = now
        db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    if not user or not user.is_active:
        revoke_all_user_refresh_tokens(db, rt.user_id)
        db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Rotate refresh token
    ttl = get_refresh_ttl_for_role(user.role)
    raw_new = generate_refresh_token()
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_new),
        device_label=(rt.device_label or ua)[:255],
        expires_at=now + ttl,
    )
    db.add(new_rt)
    db.flush()

    rt.revoked_at = now
    rt.replaced_by_id = new_rt.id
    db.commit()

    access_token = create_access_token(user_id=user.id, role=user.role)
    _set_refresh_cookie(response, raw_new, ttl)

    return TokenOut(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role,
        full_name=user.full_name,
        mobile=user.mobile,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Revoke current refresh token cookie and log logout event."""
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        token_hash = hash_refresh_token(raw_token)
        rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if rt:
            if rt.revoked_at is None:
                rt.revoked_at = datetime.now(timezone.utc)
            user = db.query(User).filter(User.id == rt.user_id).first()
            log_auth_event(
                db=db,
                action="logout",
                mobile=user.mobile if user else "unknown",
                ip=_client_ip(request),
                user_agent=_user_agent(request),
                user_id=rt.user_id,
            )
            db.commit()

    _clear_refresh_cookie(response)
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """Only Admin and Owner can view full user roster."""
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """Admin/Owner adds a new staff user with normalized +91 mobile, name, and role."""
    try:
        mobile = normalize_mobile(data.mobile)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    existing = db.query(User).filter(User.mobile == mobile).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this mobile number already exists.",
        )

    user = User(
        mobile=mobile,
        full_name=data.full_name.strip(),
        role=data.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER])),
):
    """
    Admin/Owner updates a user's name, role, or active status.
    Deactivating revokes all refresh tokens immediately.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.full_name is not None:
        user.full_name = data.full_name.strip()
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
        if not data.is_active:
            revoke_all_user_refresh_tokens(db, user.id)

    db.commit()
    db.refresh(user)
    return user
