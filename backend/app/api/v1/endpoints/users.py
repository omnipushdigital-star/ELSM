from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID

from app.db.session import get_db
from app.models.models import User, UserRole, AuditLog
from app.core.security import hash_password
from app.core.deps import get_current_user, require_roles

router = APIRouter(prefix="/users", tags=["User Management"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    role: UserRole
    location_id: Optional[UUID] = None
    employee_id: Optional[str] = None
    imei_number: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    location_id: Optional[UUID] = None
    imei_number: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    role: UserRole
    is_active: bool
    is_2fa_enabled: bool
    employee_id: Optional[str]
    location_id: Optional[UUID]
    imei_number: Optional[str]

    class Config:
        from_attributes = True


class IMEIRebindRequest(BaseModel):
    new_imei: str
    reason: str


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        location_id=payload.location_id,
        employee_id=payload.employee_id,
        imei_number=payload.imei_number,
    )
    db.add(user)

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action="USER_CREATED",
        entity_type="User",
        user_role=current_user.role.value,
        after_state={"email": payload.email, "role": payload.role.value},
    )
    db.add(log)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = Query(None),
    location_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN, UserRole.NODAL_OFFICER
    )),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if location_id:
        query = query.where(User.location_id == location_id)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before_state = {"name": user.name, "is_active": user.is_active}
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    log = AuditLog(
        user_id=current_user.id,
        action="USER_UPDATED",
        entity_type="User",
        entity_id=user_id,
        user_role=current_user.role.value,
        before_state=before_state,
        after_state=payload.model_dump(exclude_none=True),
    )
    db.add(log)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/{user_id}/rebind-imei")
async def rebind_imei(
    user_id: UUID,
    payload: IMEIRebindRequest,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """IMEI re-binding for field engineers (Clause 2.6)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_imei = user.imei_number
    user.imei_number = payload.new_imei

    log = AuditLog(
        user_id=current_user.id,
        action="IMEI_REBOUND",
        entity_type="User",
        entity_id=user_id,
        user_role=current_user.role.value,
        before_state={"imei": old_imei},
        after_state={"imei": payload.new_imei, "reason": payload.reason},
    )
    db.add(log)
    await db.commit()

    return {"message": "IMEI rebound successfully", "new_imei": payload.new_imei}


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    log = AuditLog(
        user_id=current_user.id,
        action="USER_DEACTIVATED",
        entity_type="User",
        entity_id=user_id,
        user_role=current_user.role.value,
    )
    db.add(log)
    await db.commit()

    return {"message": "User deactivated successfully"}
