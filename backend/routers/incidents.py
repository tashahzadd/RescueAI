from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from agents import intake_agent, orchestrator

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def log_audit(db: Session, incident_id: Optional[str], actor: str, action: str, details: dict = None):
    entry = models.AuditLog(incident_id=incident_id, actor=actor, action=action, details=details or {})
    db.add(entry)
    db.commit()


class IncidentCreateRequest(BaseModel):
    raw_text: str
    source_type: str = "CITIZEN"
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AddReportRequest(BaseModel):
    raw_text: str
    source_type: str = "CITIZEN"


@router.post("", response_model=schemas.IncidentDetailOut)
def create_incident(payload: IncidentCreateRequest, db: Session = Depends(get_db)):
    """AGENT 1 (Emergency Intake Agent) runs here to structure the raw report."""
    result = intake_agent.run_intake(
        raw_text=payload.raw_text,
        location=payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        source_type=payload.source_type,
    )

    incident = models.Incident(
        incident_type=result["incident_type"],
        description=payload.raw_text,
        location=result["location"],
        latitude=result["latitude"],
        longitude=result["longitude"],
        hazards=result["hazards"],
        estimated_victims_min=result["estimated_victims_min"],
        estimated_victims_max=result["estimated_victims_max"],
        confidence=result["confidence"],
        status=models.IncidentStatus.NEW.value,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    reliability = orchestrator.reliability_for_source(payload.source_type)
    report = models.IncidentReport(
        incident_id=incident.id,
        raw_text=payload.raw_text,
        source_type=payload.source_type,
        reliability=reliability,
        extracted_victims=result["estimated_victims_max"],
    )
    db.add(report)
    db.commit()

    log_audit(db, incident.id, "AI_SYSTEM", "INCIDENT_CREATED", {"incident_type": incident.incident_type})

    db.refresh(incident)
    return incident


@router.post("/{incident_id}/reports", response_model=schemas.IncidentDetailOut)
def add_report(incident_id: str, payload: AddReportRequest, db: Session = Depends(get_db)):
    """Add an additional report to an existing incident (used to demo conflict detection)."""
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    intake_result = intake_agent.run_intake(raw_text=payload.raw_text, source_type=payload.source_type)
    reliability = orchestrator.reliability_for_source(payload.source_type)

    report = models.IncidentReport(
        incident_id=incident.id,
        raw_text=payload.raw_text,
        source_type=payload.source_type,
        reliability=reliability,
        extracted_victims=intake_result["estimated_victims_max"],
    )
    db.add(report)
    db.commit()

    all_reports = db.query(models.IncidentReport).filter(models.IncidentReport.incident_id == incident.id).all()
    conflicting, notes, vmin, vmax = orchestrator.detect_conflicts(all_reports)

    incident.conflicting_info = conflicting
    incident.conflict_notes = notes
    if vmin is not None:
        incident.estimated_victims_min = vmin
        incident.estimated_victims_max = vmax
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)

    log_audit(db, incident.id, "AI_SYSTEM", "REPORT_ADDED", {"conflicting_info": conflicting})
    return incident


@router.get("", response_model=List[schemas.IncidentOut])
def list_incidents(status: Optional[str] = None, severity: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Incident)
    if status:
        q = q.filter(models.Incident.status == status)
    if severity:
        q = q.filter(models.Incident.severity == severity)
    return q.order_by(models.Incident.created_at.desc()).all()


@router.get("/{incident_id}", response_model=schemas.IncidentDetailOut)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/analyze", response_model=schemas.ResponsePlanOut)
def analyze_incident(incident_id: str, db: Session = Depends(get_db)):
    """
    Runs AGENTS 2-6 (Situation Analysis, Risk Assessment, Resource Allocation,
    Hospital Coordination, Response Planning) and produces a response plan
    awaiting human approval.
    """
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = models.IncidentStatus.ANALYZING.value
    db.commit()

    reports = db.query(models.IncidentReport).filter(models.IncidentReport.incident_id == incident.id).all()
    available_resources = db.query(models.Resource).filter(models.Resource.status == models.ResourceStatus.AVAILABLE.value).all()
    hospitals = db.query(models.Hospital).all()

    pipeline_result = orchestrator.run_full_pipeline(incident, reports, available_resources, hospitals)
    plan_data = pipeline_result["plan"]

    incident.severity = plan_data["severity"]
    incident.status = models.IncidentStatus.AWAITING_APPROVAL.value
    incident.confidence = {**(incident.confidence or {}), **plan_data["confidence"]}
    db.commit()

    plan = models.ResponsePlan(
        incident_id=incident.id,
        summary=plan_data["summary"],
        severity=plan_data["severity"],
        recommended_resources=plan_data["recommended_resources"],
        recommended_hospital=plan_data["recommended_hospital"],
        risks=plan_data["risks"],
        actions=plan_data["actions"],
        information_gaps=plan_data["information_gaps"],
        knowledge_base_refs=plan_data["knowledge_base_refs"],
        confidence=plan_data["confidence"],
        explainability=plan_data["explainability"],
        approval_status=models.ApprovalStatus.PENDING.value,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    log_audit(db, incident.id, "AI_SYSTEM", "AI_ANALYSIS_COMPLETE", {"severity": plan_data["severity"]})
    log_audit(db, incident.id, "AI_SYSTEM", "RESPONSE_PLAN_GENERATED", {"plan_id": plan.id})

    return plan


@router.get("/{incident_id}/response-plan", response_model=schemas.ResponsePlanOut)
def get_response_plan(incident_id: str, db: Session = Depends(get_db)):
    plan = (
        db.query(models.ResponsePlan)
        .filter(models.ResponsePlan.incident_id == incident_id)
        .order_by(models.ResponsePlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No response plan found for this incident")
    return plan


@router.post("/{incident_id}/approve", response_model=schemas.ResponsePlanOut)
def approve_response(incident_id: str, payload: schemas.ApproveRequest, db: Session = Depends(get_db)):
    """
    Human-in-the-loop approval. Only after this call does the system simulate
    dispatch - the AI itself never marks anything as dispatched.
    """
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    plan = (
        db.query(models.ResponsePlan)
        .filter(models.ResponsePlan.incident_id == incident_id)
        .order_by(models.ResponsePlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No response plan to approve")

    plan.approval_status = models.ApprovalStatus.MODIFIED.value if payload.modifications else models.ApprovalStatus.APPROVED.value
    plan.approved_by = payload.approved_by
    db.commit()

    # --- SIMULATED DISPATCH ---
    for rec in plan.recommended_resources:
        for chosen in rec.get("chosen", []):
            resource = db.query(models.Resource).filter(models.Resource.id == chosen["id"]).first()
            if resource and resource.status == models.ResourceStatus.AVAILABLE.value:
                resource.status = models.ResourceStatus.DISPATCHED.value
                resource.current_workload += 1
                assignment = models.ResourceAssignment(
                    incident_id=incident.id,
                    resource_id=resource.id,
                    response_plan_id=plan.id,
                    status="DISPATCHED",
                )
                db.add(assignment)
                notif = models.Notification(
                    incident_id=incident.id,
                    message=f"[SIMULATED] {resource.name} assigned to Incident #{incident.id[:8]}.",
                    is_simulated=True,
                )
                db.add(notif)

    incident.status = models.IncidentStatus.DISPATCHED.value
    db.commit()
    db.refresh(plan)

    log_audit(db, incident.id, payload.approved_by, "RESPONSE_APPROVED", {"plan_id": plan.id})
    log_audit(db, incident.id, "SYSTEM", "SIMULATED_DISPATCH", {"plan_id": plan.id})

    return plan


@router.post("/{incident_id}/reject", response_model=schemas.ResponsePlanOut)
def reject_response(incident_id: str, payload: schemas.RejectRequest, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    plan = (
        db.query(models.ResponsePlan)
        .filter(models.ResponsePlan.incident_id == incident_id)
        .order_by(models.ResponsePlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No response plan to reject")

    plan.approval_status = models.ApprovalStatus.REJECTED.value
    plan.approved_by = payload.rejected_by
    incident.status = models.IncidentStatus.REJECTED.value
    db.commit()
    db.refresh(plan)

    log_audit(db, incident.id, payload.rejected_by, "RESPONSE_REJECTED", {"reason": payload.reason})
    return plan


@router.post("/{incident_id}/resolve", response_model=schemas.IncidentOut)
def resolve_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = models.IncidentStatus.RESOLVED.value
    db.commit()
    db.refresh(incident)
    log_audit(db, incident.id, "SYSTEM", "INCIDENT_RESOLVED", {})
    return incident
