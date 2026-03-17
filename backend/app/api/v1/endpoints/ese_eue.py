from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.models.models import User, UserRole, AuditLog, ESEUERequest, LockEvent, SLARecord, ELock, Machine, EventType, RequestStatus, UnlockMethod
from app.core.deps import get_current_user, require_roles

router = APIRouter(prefix="/ese-eue", tags=["ESE/EUE Workflow"])

def _working_days_deadline(from_dt, days):
    current = from_dt
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current

def _generate_request_number(event_type):
    prefix = event_type.value.upper()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")
    return f"{prefix}-{date_str}-{rand_suffix}"

async def _audit(db, user, action, entity_type, entity_id=None, before=None, after=None):
    log = AuditLog(user_id=user.id, action=action, entity_type=entity_type, entity_id=entity_id, user_role=user.role.value, before_state=before, after_state=after)
    db.add(log)

class RequestCreate(BaseModel):
    event_type: EventType
    machine_id: UUID
    e_lock_id: Optional[UUID] = None
    notes: Optional[str] = None

class RequestApprove(BaseModel):
    notes: Optional[str] = None

class RequestReject(BaseModel):
    rejection_reason: str

class RequestAssign(BaseModel):
    engineer_id: UUID

class LockEventCreate(BaseModel):
    unlock_method: UnlockMethod
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    notes: Optional[str] = None

class SLARecordOut(BaseModel):
    sla_deadline: datetime
    completed_at: Optional[datetime] = None
    is_breached: bool
    breach_duration_hours: Optional[float] = None
    penalty_amount: float
    class Config:
        from_attributes = True

class LockEventOut(BaseModel):
    id: UUID
    event_type: EventType
    unlock_method: Optional[UnlockMethod] = None
    event_timestamp: datetime
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    otp_used: bool
    notes: Optional[str] = None
    class Config:
        from_attributes = True

class RequestOut(BaseModel):
    id: UUID
    request_number: str
    event_type: EventType
    machine_id: UUID
    e_lock_id: Optional[UUID] = None
    status: RequestStatus
    created_by_id: UUID
    approved_by_id: Optional[UUID] = None
    assigned_engineer_id: Optional[UUID] = None
    requested_at: datetime
    approved_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None
    is_sla_breached: bool
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    photo_evidence_urls: List[str]
    class Config:
        from_attributes = True

class RequestDetailOut(RequestOut):
    sla_record: Optional[SLARecordOut] = None
    lock_event: Optional[LockEventOut] = None

class RequestSummary(BaseModel):
    total: int
    pending: int
    approved: int
    in_progress: int
    completed: int
    sla_breached: int
    rejected: int

@router.post("/", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def create_request(payload: RequestCreate, current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN, UserRole.NODAL_OFFICER)), db: AsyncSession = Depends(get_db)):
    machine = await db.get(Machine, payload.machine_id)
    if not machine or not machine.is_active:
        raise HTTPException(status_code=404, detail="Machine not found or inactive")
    now = datetime.now(timezone.utc)
    req = ESEUERequest(request_number=_generate_request_number(payload.event_type), event_type=payload.event_type, machine_id=payload.machine_id, e_lock_id=payload.e_lock_id, status=RequestStatus.PENDING, created_by_id=current_user.id, requested_at=now, notes=payload.notes, photo_evidence_urls=[])
    db.add(req)
    await db.flush()
    sla_deadline = _working_days_deadline(now, 3)
    sla = SLARecord(request_id=req.id, sla_deadline=sla_deadline, is_breached=False, penalty_amount=0.0)
    db.add(sla)
    req.sla_deadline = sla_deadline
    await _audit(db, current_user, "REQUEST_CREATED", "ESEUERequest", entity_id=req.id)
    await db.commit()
    await db.refresh(req)
    return req

@router.get("/summary", response_model=RequestSummary)
async def get_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ESEUERequest.status, func.count(ESEUERequest.id)).group_by(ESEUERequest.status))
    rows = result.all()
    counts = {row[0]: row[1] for row in rows}
    total = sum(counts.values())
    return RequestSummary(total=total, pending=counts.get(RequestStatus.PENDING, 0), approved=counts.get(RequestStatus.APPROVED, 0), in_progress=counts.get(RequestStatus.IN_PROGRESS, 0), completed=counts.get(RequestStatus.COMPLETED, 0), sla_breached=counts.get(RequestStatus.SLA_BREACHED, 0), rejected=counts.get(RequestStatus.REJECTED, 0))

@router.get("/", response_model=List[RequestOut])
async def list_requests(event_type: Optional[EventType] = Query(None), status_filter: Optional[RequestStatus] = Query(None, alias="status"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(ESEUERequest)
    if event_type:
        query = query.where(ESEUERequest.event_type == event_type)
    if status_filter:
        query = query.where(ESEUERequest.status == status_filter)
    query = query.order_by(ESEUERequest.requested_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{request_id}", response_model=RequestDetailOut)
async def get_request(request_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ESEUERequest).options(selectinload(ESEUERequest.sla_record), selectinload(ESEUERequest.lock_event)).where(ESEUERequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

@router.post("/{request_id}/approve", response_model=RequestOut)
async def approve_request(request_id: UUID, payload: RequestApprove, current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN)), db: AsyncSession = Depends(get_db)):
    req = await db.get(ESEUERequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is not pending")
    req.status = RequestStatus.APPROVED
    req.approved_by_id = current_user.id
    req.approved_at = datetime.now(timezone.utc)
    await _audit(db, current_user, "REQUEST_APPROVED", "ESEUERequest", entity_id=req.id)
    await db.commit()
    await db.refresh(req)
    return req

@router.post("/{request_id}/reject", response_model=RequestOut)
async def reject_request(request_id: UUID, payload: RequestReject, current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN)), db: AsyncSession = Depends(get_db)):
    req = await db.get(ESEUERequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = RequestStatus.REJECTED
    req.rejection_reason = payload.rejection_reason
    await _audit(db, current_user, "REQUEST_REJECTED", "ESEUERequest", entity_id=req.id)
    await db.commit()
    await db.refresh(req)
    return req

@router.post("/{request_id}/assign", response_model=RequestOut)
async def assign_engineer(request_id: UUID, payload: RequestAssign, current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN, UserRole.NODAL_OFFICER)), db: AsyncSession = Depends(get_db)):
    req = await db.get(ESEUERequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Request must be approved first")
    req.assigned_engineer_id = payload.engineer_id
    req.assigned_at = datetime.now(timezone.utc)
    req.status = RequestStatus.ASSIGNED
    await _audit(db, current_user, "REQUEST_ASSIGNED", "ESEUERequest", entity_id=req.id)
    await db.commit()
    await db.refresh(req)
    return req

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

class RequestComplete(BaseModel):
    status: str
    notes: Optional[str] = None

@router.patch("/{request_id}", response_model=RequestOut)
async def update_request_status(
    request_id: UUID,
    payload: RequestComplete,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN,
        UserRole.NODAL_OFFICER, UserRole.FIELD_ENGINEER
    )),
    db: AsyncSession = Depends(get_db),
):
    """Complete or update a request. FIELD_ENGINEER can only complete their own assigned requests."""
    req = await db.get(ESEUERequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    new_status = payload.status.lower()

    if current_user.role == UserRole.FIELD_ENGINEER:
        if req.assigned_engineer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Can only update your own assigned requests")

    valid = {
        RequestStatus.APPROVED:    ["in_progress", "completed"],
        RequestStatus.ASSIGNED:    ["in_progress", "completed"],
        RequestStatus.IN_PROGRESS: ["completed"],
    }
    allowed = valid.get(req.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {req.status.value} to {new_status}. Allowed: {allowed}"
        )

    now = datetime.now(timezone.utc)
    if new_status == "in_progress":
        req.status = RequestStatus.IN_PROGRESS
    elif new_status == "completed":
        req.status = RequestStatus.COMPLETED
        req.completed_at = now
        # Check SLA breach
        if req.sla_deadline and now > req.sla_deadline:
            req.is_sla_breached = True
            req.status = RequestStatus.SLA_BREACHED
        # Update SLA record
        sla_res = await db.execute(select(SLARecord).where(SLARecord.request_id == req.id))
        sla_rec = sla_res.scalar_one_or_none()
        if sla_rec:
            sla_rec.completed_at = now
            if req.is_sla_breached:
                sla_rec.is_breached = True
                sla_rec.breach_duration_hours = round((now - req.sla_deadline).total_seconds() / 3600, 2)

    if payload.notes:
        req.notes = (req.notes or "") + f"\n[{current_user.name}]: {payload.notes}"

    await _audit(db, current_user, "REQUEST_STATUS_UPDATED", "ESEUERequest", entity_id=req.id,
                 after={"status": new_status})
    await db.commit()
    await db.refresh(req)
    return req
