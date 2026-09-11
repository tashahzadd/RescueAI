from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Incident intake
# ---------------------------------------------------------------------------

class IncidentReportCreate(BaseModel):
    raw_text: str
    source_type: str = Field(default="CITIZEN", description="FIELD_OFFICER, VERIFIED_ORG, EMERGENCY_OPERATOR, CITIZEN, SOCIAL_MEDIA")
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class IncidentReportOut(BaseModel):
    id: str
    raw_text: str
    source_type: str
    reliability: str
    extracted_victims: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentOut(BaseModel):
    id: str
    incident_type: str
    description: str
    location: str
    latitude: float
    longitude: float
    severity: Optional[str]
    estimated_victims_min: Optional[int]
    estimated_victims_max: Optional[int]
    hazards: List[str] = []
    status: str
    confidence: Dict[str, Any] = {}
    conflicting_info: bool
    conflict_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentDetailOut(IncidentOut):
    reports: List[IncidentReportOut] = []


class ResponsePlanOut(BaseModel):
    id: str
    incident_id: str
    summary: str
    severity: str
    recommended_resources: List[Dict[str, Any]] = []
    recommended_hospital: Dict[str, Any] = {}
    risks: List[str] = []
    actions: List[str] = []
    information_gaps: List[str] = []
    knowledge_base_refs: List[str] = []
    confidence: Dict[str, Any] = {}
    explainability: Dict[str, Any] = {}
    approval_status: str
    approved_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ResourceOut(BaseModel):
    id: str
    name: str
    resource_type: str
    status: str
    latitude: float
    longitude: float
    capabilities: List[str] = []
    equipment: List[str] = []
    capacity: int
    current_workload: int
    organization: Optional[str]
    trust_level: str = "DEMO"

    class Config:
        from_attributes = True


class HospitalOut(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    emergency_beds: int
    icu_beds: int
    trauma_capacity: str
    current_load: int
    status: str
    district: Optional[str] = None
    facility_type: Optional[str] = None
    ownership: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    trust_level: str = "DEMO"
    last_verified: Optional[str] = None

    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    approved_by: str = Field(description="Name/id of the authorized human approver")
    modifications: Optional[Dict[str, Any]] = None


class RejectRequest(BaseModel):
    rejected_by: str
    reason: Optional[str] = None


class DashboardStats(BaseModel):
    active_incidents: int
    critical_incidents: int
    high_incidents: int
    ambulances_available: int
    rescue_teams_available: int
    fire_units_available: int
    pending_approvals: int
    resolved_incidents: int


class AuditLogOut(BaseModel):
    id: str
    incident_id: Optional[str]
    actor: str
    action: str
    details: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True
