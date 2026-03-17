"""
ELSM - Complete Database Models
All tables for the Electronic Lock Solution Management Portal
"""

import uuid
import enum
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text,
    ForeignKey, Enum, DateTime, JSON, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, UUIDMixin


# ─── ENUMS ───────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"           # Customer Central NOC
    BSNL_ADMIN = "bsnl_admin"             # BSNL SPOC/PM
    NODAL_OFFICER = "nodal_officer"       # Per-location officer
    FIELD_ENGINEER = "field_engineer"     # IMT field engineer
    AUDITOR = "auditor"                   # Read-only auditor


class LockStatus(str, enum.Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    TAMPERED = "tampered"
    OFFLINE = "offline"
    CHARGING = "charging"


class EventType(str, enum.Enum):
    ESE = "ese"   # Electronic Sealing Event
    EUE = "eue"   # Electronic Unsealing Event
    VE = "ve"     # Visit Event


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    SLA_BREACHED = "sla_breached"


class AlertType(str, enum.Enum):
    LOW_BATTERY = "low_battery"
    TAMPER = "tamper"
    GEO_FENCE = "geo_fence"
    OFFLINE = "offline"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ANTI_CUT = "anti_cut"
    ILLEGAL_DEMOLITION = "illegal_demolition"


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UCStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"


class UnlockMethod(str, enum.Enum):
    RFID = "rfid"
    OTP = "otp"
    APP = "app"
    WEB = "web"
    BLUETOOTH = "bluetooth"
    SMS = "sms"


# ─── USER & AUTH ─────────────────────────────────────────────────────────────

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(64), nullable=True)
    imei_number = Column(String(20), nullable=True)       # For field engineers (mobile app binding)
    employee_id = Column(String(50), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    location = relationship("Location", back_populates="users")
    assigned_requests = relationship("ESEUERequest", back_populates="assigned_engineer",
                                     foreign_keys="ESEUERequest.assigned_engineer_id")
    created_requests = relationship("ESEUERequest", back_populates="created_by",
                                    foreign_keys="ESEUERequest.created_by_id")
    audit_logs = relationship("AuditLog", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(512), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")


# ─── LOCATION & MACHINE ──────────────────────────────────────────────────────

class Location(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "locations"

    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)   # Range/Division/Commissionerate code
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    zone = Column(String(100), nullable=True)
    division = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="location")
    machines = relationship("Machine", back_populates="location")
    geo_fences = relationship("GeoFence", back_populates="location")


class Machine(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "machines"

    name = Column(String(200), nullable=False)
    machine_id = Column(String(100), unique=True, nullable=False)   # Physical machine ID
    machine_type = Column(String(100), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    current_lock_id = Column(UUID(as_uuid=True), ForeignKey("e_locks.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Relationships
    location = relationship("Location", back_populates="machines")
    current_lock = relationship("ELock", foreign_keys=[current_lock_id])
    ese_eue_requests = relationship("ESEUERequest", back_populates="machine")


# ─── E-LOCK DEVICE ───────────────────────────────────────────────────────────

class ELock(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "e_locks"

    device_id = Column(String(100), unique=True, nullable=False, index=True)  # Hardware serial
    imei = Column(String(20), unique=True, nullable=True)
    sim1_number = Column(String(15), nullable=True)
    sim2_number = Column(String(15), nullable=True)
    sim1_active = Column(Boolean, default=True)
    sim2_active = Column(Boolean, default=True)
    firmware_version = Column(String(50), nullable=True)
    hardware_version = Column(String(50), nullable=True)
    manufacture_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(LockStatus), default=LockStatus.UNLOCKED)
    battery_level = Column(Integer, default=100)               # Percentage
    last_ping = Column(DateTime(timezone=True), nullable=True)
    last_gps_lat = Column(Float, nullable=True)
    last_gps_lng = Column(Float, nullable=True)
    is_deployed = Column(Boolean, default=False)
    assigned_machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    failure_count_6months = Column(Integer, default=0)   # For clause 1.12 tracking

    # Relationships
    battery_logs = relationship("BatteryLog", back_populates="e_lock")
    alerts = relationship("Alert", back_populates="e_lock")
    lock_events = relationship("LockEvent", back_populates="e_lock")
    health_pings = relationship("HealthPing", back_populates="e_lock")


class HealthPing(Base, UUIDMixin):
    """Daily health ping from e-Lock device (Clause 1.6b)"""
    __tablename__ = "health_pings"

    e_lock_id = Column(UUID(as_uuid=True), ForeignKey("e_locks.id"), nullable=False)
    pinged_at = Column(DateTime(timezone=True), server_default=func.now())
    battery_level = Column(Integer, nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    sim1_status = Column(Boolean, default=True)
    sim2_status = Column(Boolean, default=True)
    lock_status = Column(Enum(LockStatus), nullable=True)
    signal_strength = Column(Integer, nullable=True)
    raw_payload = Column(JSON, nullable=True)

    e_lock = relationship("ELock", back_populates="health_pings")


class BatteryLog(Base, UUIDMixin):
    """Battery level history for monitoring and alerts"""
    __tablename__ = "battery_logs"

    e_lock_id = Column(UUID(as_uuid=True), ForeignKey("e_locks.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    battery_level = Column(Integer, nullable=False)
    alert_triggered = Column(Boolean, default=False)
    charging_dispatched = Column(Boolean, default=False)

    e_lock = relationship("ELock", back_populates="battery_logs")


# ─── ESE/EUE WORKFLOW ────────────────────────────────────────────────────────

class ESEUERequest(Base, UUIDMixin, TimestampMixin):
    """Electronic Sealing/Unsealing Event Request (Clause 10.5)"""
    __tablename__ = "ese_eue_requests"

    request_number = Column(String(50), unique=True, nullable=False)   # Auto-generated ref number
    event_type = Column(Enum(EventType), nullable=False)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=False)
    e_lock_id = Column(UUID(as_uuid=True), ForeignKey("e_locks.id"), nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_engineer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # SLA tracking
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)      # 3 working days from Day 1
    is_sla_breached = Column(Boolean, default=False)

    # Event details
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    photo_evidence_urls = Column(JSON, default=list)                   # List of MinIO URLs

    # Relationships
    machine = relationship("Machine", back_populates="ese_eue_requests")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_requests")
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    assigned_engineer = relationship("User", foreign_keys=[assigned_engineer_id],
                                     back_populates="assigned_requests")
    lock_event = relationship("LockEvent", back_populates="request", uselist=False)
    sla_record = relationship("SLARecord", back_populates="request", uselist=False)


class LockEvent(Base, UUIDMixin, TimestampMixin):
    """Recorded lock/unlock event with full audit data (Clause 2.6)"""
    __tablename__ = "lock_events"

    request_id = Column(UUID(as_uuid=True), ForeignKey("ese_eue_requests.id"), nullable=False)
    e_lock_id = Column(UUID(as_uuid=True), ForeignKey("e_locks.id"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    unlock_method = Column(Enum(UnlockMethod), nullable=True)
    performed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Audit data
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    photo_urls = Column(JSON, default=list)
    rfid_card_id = Column(String(100), nullable=True)
    otp_used = Column(Boolean, default=False)
    device_imei = Column(String(20), nullable=True)      # IMEI of mobile used
    notes = Column(Text, nullable=True)

    # Relationships
    request = relationship("ESEUERequest", back_populates="lock_event")
    e_lock = relationship("ELock", back_populates="lock_events")
    performed_by = relationship("User", foreign_keys=[performed_by_id])
    officer = relationship("User", foreign_keys=[officer_id])


# ─── ALERTS ──────────────────────────────────────────────────────────────────

class Alert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alerts"

    e_lock_id = Column(UUID(as_uuid=True), ForeignKey("e_locks.id"), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notified_via_email = Column(Boolean, default=False)
    notified_via_sms = Column(Boolean, default=False)
    alert_metadata = Column("metadata", JSON, nullable=True)

    e_lock = relationship("ELock", back_populates="alerts")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])


# ─── GEO-FENCE ───────────────────────────────────────────────────────────────

class GeoFence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "geo_fences"

    name = Column(String(200), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    boundary_coordinates = Column(JSON, nullable=False)    # List of {lat, lng} points (polygon)
    radius_meters = Column(Float, nullable=True)           # For circular geo-fences
    is_active = Column(Boolean, default=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    location = relationship("Location", back_populates="geo_fences")
    created_by = relationship("User", foreign_keys=[created_by_id])


# ─── SLA TRACKING ────────────────────────────────────────────────────────────

class SLARecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sla_records"

    request_id = Column(UUID(as_uuid=True), ForeignKey("ese_eue_requests.id"), nullable=False, unique=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    is_breached = Column(Boolean, default=False)
    breach_duration_hours = Column(Float, nullable=True)   # Hours overdue
    penalty_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    request = relationship("ESEUERequest", back_populates="sla_record")


# ─── BILLING & UC ────────────────────────────────────────────────────────────

class UtilizationCertificate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "utilization_certificates"

    uc_number = Column(String(50), unique=True, nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    total_ese = Column(Integer, default=0)
    total_eue = Column(Integer, default=0)
    total_visits = Column(Integer, default=0)
    total_locks_deployed = Column(Integer, default=0)
    status = Column(Enum(UCStatus), default=UCStatus.PENDING)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    dispute_notes = Column(Text, nullable=True)
    pdf_url = Column(String(500), nullable=True)

    location = relationship("Location")
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    invoice = relationship("Invoice", back_populates="uc", uselist=False)


class Invoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoices"

    invoice_number = Column(String(50), unique=True, nullable=False)
    uc_id = Column(UUID(as_uuid=True), ForeignKey("utilization_certificates.id"), nullable=False)
    billing_period_start = Column(DateTime(timezone=True), nullable=False)
    billing_period_end = Column(DateTime(timezone=True), nullable=False)
    subtotal = Column(Float, nullable=False)
    sla_penalty_deduction = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    payment_reference = Column(String(200), nullable=True)

    uc = relationship("UtilizationCertificate", back_populates="invoice")


# ─── AUDIT LOG ───────────────────────────────────────────────────────────────

class AuditLog(Base, UUIDMixin):
    """Immutable audit trail - role-logged, time-stamped, geo-tagged (Clause 2.9)"""
    __tablename__ = "audit_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(200), nullable=False)           # e.g. "LOCK_SEALED", "USER_CREATED"
    entity_type = Column(String(100), nullable=True)       # e.g. "ESEUERequest", "ELock"
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    ip_address = Column(String(50), nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    user_role = Column(String(50), nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs")