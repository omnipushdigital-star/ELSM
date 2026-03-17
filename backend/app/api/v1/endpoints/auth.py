from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr
from typing import Optional
import qrcode
import io
import base64

from app.db.session import get_db
from app.models.models import User, RefreshToken, AuditLog
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    generate_totp_secret, get_totp_uri, verify_totp
)
from app.core.config import settings
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_2fa: bool = False
    user_id: str
    role: str
    name: str


class RefreshRequest(BaseModel):
    refresh_token: str


class Enable2FAResponse(BaseModel):
    totp_secret: str
    qr_code_base64: str
    provisioning_uri: str


class Verify2FARequest(BaseModel):
    totp_code: str


# ─── Helpers ────────────────────────────────────────────────────────────────

async def log_audit(db, user_id, action, ip_address, notes=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type="User",
        entity_id=user_id,
        ip_address=ip_address,
        user_role=None,
        notes=notes,
    )
    db.add(log)


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    # 2FA check
    if user.is_2fa_enabled:
        if not payload.totp_code:
            return LoginResponse(
                access_token="",
                refresh_token="",
                requires_2fa=True,
                user_id=str(user.id),
                role=user.role.value,
                name=user.name,
            )
        if not verify_totp(user.totp_secret, payload.totp_code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    # Generate tokens
    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token_str = create_refresh_token()

    # Store refresh token
    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token)

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    await log_audit(db, user.id, "USER_LOGIN", request.client.host)
    await db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        requires_2fa=False,
        user_id=str(user.id),
        role=user.role.value,
        name=user.name,
    )


@router.post("/refresh")
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == payload.refresh_token,
            RefreshToken.is_revoked == False,
        )
    )
    token_obj = result.scalar_one_or_none()

    if not token_obj or token_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == token_obj.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access_token = create_access_token(str(user.id), user.role.value)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    payload: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    )
    token_obj = result.scalar_one_or_none()
    if token_obj:
        token_obj.is_revoked = True
        await db.commit()

    return {"message": "Logged out successfully"}


@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled")

    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email)

    # Generate QR code
    qr = qrcode.QRCode()
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Save secret (not yet enabled until verified)
    current_user.totp_secret = secret
    await db.commit()

    return Enable2FAResponse(
        totp_secret=secret,
        qr_code_base64=qr_base64,
        provisioning_uri=uri,
    )


@router.post("/2fa/verify")
async def verify_2fa(
    payload: Verify2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA setup not initiated")

    if not verify_totp(current_user.totp_secret, payload.totp_code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    current_user.is_2fa_enabled = True
    await db.commit()

    return {"message": "2FA enabled successfully"}
