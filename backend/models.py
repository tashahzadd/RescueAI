import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import relationship

from database import Base


def gen_id():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enums (kept as plain strings in DB for SQLite/Postgres portability, but
# constrained in the Pydantic schemas layer)
# ---------------------------------------------------------------------------

class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    COMMANDER = "COMMANDER"
    DISPATCHER = "DISPATCHER"
    FIELD_RESPONDER = "FIELD_RESPONDER"
    HOSPITAL_COORDINATOR = "HOSPITAL_COORDINATOR"
    VIEWER = "VIEWER"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, enum.Enum):
    NEW = "NEW"
    ANALYZING = "ANALYZING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    DISPATCHED = "DISPATCHED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class ResourceStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    DISPATCHED = "DISPATCHED"
    ON_SCENE = "ON_SCENE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class SourceReliability(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    MODIFIED = "MODIFIED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False, default=Role.VIEWER.value)
    created_at = Column(DateTime, default=datetime.utcnow)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=gen_id)
    incident_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(String, nullable=True)
    estimated_victims_min = Column(Integer, nullable=True)
    estimated_victims_max = Column(Integer, nullable=True)
    hazards = Column(JSON, default=list)
    status = Column(String, default=IncidentStatus.NEW.value)
    confidence = Column(JSON, default=dict)  # per-field confidence scores
    conflicting_info = Column(Boolean, default=False)
    conflict_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reports = relationship("IncidentReport", back_populates="incident", cascade="all, delete-orphan")
    response_plans = relationship("ResponsePlan", back_populates="incident", cascade="all, delete-orphan")
    assignments = relationship("ResourceAssignment", back_populates="incident", cascade="all, delete-orphan")


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(String, primary_key=True, default=gen_id)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    raw_text = Column(Text, nullable=False)
    source_type = Column(String, nullable=False)  # e.g. FIELD_OFFICER, CITIZEN, SOCIAL_MEDIA
    reliability = Column(String, nullable=False, default=SourceReliability.MEDIUM.value)
    extracted_victims = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("Incident", back_populates="reports")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    status = Column(String, default=ResourceStatus.AVAILABLE.value)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capabilities = Column(JSON, default=list)
    equipment = Column(JSON, default=list)
    capacity = Column(Integer, default=1)
    current_workload = Column(Integer, default=0)
    organization = Column(String, nullable=True)
    # Provenance / data-trust fields (see backend/data/SOURCES.md)
    trust_level = Column(String, default="DEMO")  # OFFICIAL / LIVE / REPORTED / PUBLIC / DEMO

    assignments = relationship("ResourceAssignment", back_populates="resource")


class ResourceAssignment(Base):
    __tablename__ = "resource_assignments"

    id = Column(String, primary_key=True, default=gen_id)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False)
    response_plan_id = Column(String, ForeignKey("response_plans.id"), nullable=True)
    status = Column(String, default="ASSIGNED")
    assigned_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("Incident", back_populates="assignments")
    resource = relationship("Resource", back_populates="assignments")


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    emergency_beds = Column(Integer, default=0)
    icu_beds = Column(Integer, default=0)
    trauma_capacity = Column(String, default="MEDIUM")  # LOW/MEDIUM/HIGH
    current_load = Column(Integer, default=0)
    status = Column(String, default="OPERATIONAL")
    district = Column(String, nullable=True)
    facility_type = Column(String, nullable=True)
    ownership = Column(String, nullable=True)
    # Provenance / data-trust fields (see backend/data/SOURCES.md) -
    # the AI treats bed counts as "reported", not "confirmed live",
    # unless trust_level == "LIVE".
    source_name = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    trust_level = Column(String, default="DEMO")  # OFFICIAL / LIVE / REPORTED / PUBLIC / DEMO
    last_verified = Column(String, nullable=True)


class ResponsePlan(Base):
    __tablename__ = "response_plans"

    id = Column(String, primary_key=True, default=gen_id)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    summary = Column(Text, nullable=False)
    severity = Column(String, nullable=False)
    recommended_resources = Column(JSON, default=list)
    recommended_hospital = Column(JSON, default=dict)
    risks = Column(JSON, default=list)
    actions = Column(JSON, default=list)
    information_gaps = Column(JSON, default=list)
    knowledge_base_refs = Column(JSON, default=list)
    confidence = Column(JSON, default=dict)
    explainability = Column(JSON, default=dict)
    approval_status = Column(String, default=ApprovalStatus.PENDING.value)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("Incident", back_populates="response_plans")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=gen_id)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=True)
    message = Column(Text, nullable=False)
    is_simulated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_id)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=True)
    actor = Column(String, nullable=False)  # user id/name or "AI_SYSTEM"
    action = Column(String, nullable=False)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
