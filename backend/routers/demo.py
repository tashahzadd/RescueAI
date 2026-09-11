from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
from database import get_db
from routers.incidents import log_audit
from agents import intake_agent, orchestrator

router = APIRouter(prefix="/api/demo", tags=["demo"])

DEMO_SCENARIO = {
    "raw_text": "A three-story building has collapsed near Market Road. Around 15 people may be trapped. Smoke is coming from the building.",
    "location": "Market Road, Karachi",
    "latitude": 24.8608,
    "longitude": 67.0100,
    "source_type": "EMERGENCY_OPERATOR",
}

DEMO_CONFLICTING_REPORTS = [
    {"raw_text": "20 people trapped inside the collapsed building on Market Road.", "source_type": "SOCIAL_MEDIA"},
    {"raw_text": "Field officer reports approximately 5 people confirmed inside the structure.", "source_type": "FIELD_OFFICER"},
]


@router.post("/load-scenario")
def load_demo_scenario(db: Session = Depends(get_db), include_conflicting_reports: bool = True):
    """
    One-click DEMO MODE action: creates the preloaded 'building collapse'
    scenario (optionally with conflicting follow-up reports) so judges can
    see the full pipeline without typing anything in.
    """
    result = intake_agent.run_intake(
        raw_text=DEMO_SCENARIO["raw_text"],
        location=DEMO_SCENARIO["location"],
        latitude=DEMO_SCENARIO["latitude"],
        longitude=DEMO_SCENARIO["longitude"],
        source_type=DEMO_SCENARIO["source_type"],
    )

    incident = models.Incident(
        incident_type=result["incident_type"],
        description=DEMO_SCENARIO["raw_text"],
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

    reliability = orchestrator.reliability_for_source(DEMO_SCENARIO["source_type"])
    db.add(models.IncidentReport(
        incident_id=incident.id,
        raw_text=DEMO_SCENARIO["raw_text"],
        source_type=DEMO_SCENARIO["source_type"],
        reliability=reliability,
        extracted_victims=result["estimated_victims_max"],
    ))
    db.commit()

    if include_conflicting_reports:
        for rep in DEMO_CONFLICTING_REPORTS:
            intake_result = intake_agent.run_intake(raw_text=rep["raw_text"], source_type=rep["source_type"])
            reliability = orchestrator.reliability_for_source(rep["source_type"])
            db.add(models.IncidentReport(
                incident_id=incident.id,
                raw_text=rep["raw_text"],
                source_type=rep["source_type"],
                reliability=reliability,
                extracted_victims=intake_result["estimated_victims_max"],
            ))
        db.commit()

        all_reports = db.query(models.IncidentReport).filter(models.IncidentReport.incident_id == incident.id).all()
        conflicting, notes, vmin, vmax = orchestrator.detect_conflicts(all_reports)
        incident.conflicting_info = conflicting
        incident.conflict_notes = notes
        if vmin is not None:
            incident.estimated_victims_min = vmin
            incident.estimated_victims_max = vmax
        db.commit()

    log_audit(db, incident.id, "AI_SYSTEM", "DEMO_SCENARIO_LOADED", {})
    db.refresh(incident)
    return {"incident_id": incident.id, "message": "Demo scenario loaded. Call /incidents/{id}/analyze next."}
