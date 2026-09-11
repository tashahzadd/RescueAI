from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

resources_router = APIRouter(prefix="/api/resources", tags=["resources"])
hospitals_router = APIRouter(prefix="/api/hospitals", tags=["hospitals"])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
audit_router = APIRouter(prefix="/api/audit-logs", tags=["audit"])
notifications_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@resources_router.get("", response_model=List[schemas.ResourceOut])
def list_resources(resource_type: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Resource)
    if resource_type:
        q = q.filter(models.Resource.resource_type == resource_type)
    if status:
        q = q.filter(models.Resource.status == status)
    return q.all()


@resources_router.get("/available", response_model=List[schemas.ResourceOut])
def list_available_resources(db: Session = Depends(get_db)):
    return db.query(models.Resource).filter(models.Resource.status == models.ResourceStatus.AVAILABLE.value).all()


@hospitals_router.get("", response_model=List[schemas.HospitalOut])
def list_hospitals(db: Session = Depends(get_db)):
    return db.query(models.Hospital).all()


@dashboard_router.get("/stats", response_model=schemas.DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    incidents = db.query(models.Incident).all()
    active_statuses = {
        models.IncidentStatus.NEW.value,
        models.IncidentStatus.ANALYZING.value,
        models.IncidentStatus.AWAITING_APPROVAL.value,
        models.IncidentStatus.APPROVED.value,
        models.IncidentStatus.DISPATCHED.value,
    }
    active = [i for i in incidents if i.status in active_statuses]
    critical = [i for i in active if i.severity == "CRITICAL"]
    high = [i for i in active if i.severity == "HIGH"]
    resolved = [i for i in incidents if i.status == models.IncidentStatus.RESOLVED.value]
    pending = [i for i in incidents if i.status == models.IncidentStatus.AWAITING_APPROVAL.value]

    def count_available(rtype):
        return db.query(models.Resource).filter(
            models.Resource.resource_type == rtype,
            models.Resource.status == models.ResourceStatus.AVAILABLE.value,
        ).count()

    return schemas.DashboardStats(
        active_incidents=len(active),
        critical_incidents=len(critical),
        high_incidents=len(high),
        ambulances_available=count_available("Ambulance"),
        rescue_teams_available=count_available("Rescue Team") + count_available("Search & Rescue Team"),
        fire_units_available=count_available("Fire Unit"),
        pending_approvals=len(pending),
        resolved_incidents=len(resolved),
    )


@dashboard_router.get("/analytics")
def dashboard_analytics(db: Session = Depends(get_db)):
    incidents = db.query(models.Incident).all()
    by_type = {}
    by_severity = {}
    for i in incidents:
        by_type[i.incident_type] = by_type.get(i.incident_type, 0) + 1
        if i.severity:
            by_severity[i.severity] = by_severity.get(i.severity, 0) + 1

    resources = db.query(models.Resource).all()
    resource_util = {}
    for r in resources:
        bucket = resource_util.setdefault(r.resource_type, {"total": 0, "dispatched": 0})
        bucket["total"] += 1
        if r.status == models.ResourceStatus.DISPATCHED.value:
            bucket["dispatched"] += 1

    hospitals = db.query(models.Hospital).all()
    hospital_util = [
        {"name": h.name, "load": h.current_load, "capacity": h.emergency_beds + h.icu_beds}
        for h in hospitals
    ]

    return {
        "incidents_by_type": by_type,
        "incidents_by_severity": by_severity,
        "resource_utilization": resource_util,
        "hospital_utilization": hospital_util,
        "total_incidents": len(incidents),
        "resolved_incidents": len([i for i in incidents if i.status == models.IncidentStatus.RESOLVED.value]),
    }


@audit_router.get("", response_model=List[schemas.AuditLogOut])
def list_audit_logs(incident_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.AuditLog)
    if incident_id:
        q = q.filter(models.AuditLog.incident_id == incident_id)
    return q.order_by(models.AuditLog.created_at.desc()).limit(500).all()


@notifications_router.get("")
def list_notifications(db: Session = Depends(get_db)):
    notes = db.query(models.Notification).order_by(models.Notification.created_at.desc()).limit(100).all()
    return [
        {
            "id": n.id,
            "incident_id": n.incident_id,
            "message": n.message,
            "is_simulated": n.is_simulated,
            "created_at": n.created_at,
        }
        for n in notes
    ]
