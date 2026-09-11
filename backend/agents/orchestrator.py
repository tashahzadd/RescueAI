"""
Orchestrates the multi-agent pipeline:

Intake -> Analysis -> Risk -> Resource Allocation -> Hospital Coordination
-> Response Planning

Also implements conflicting-report detection (used by the intake pipeline
before analysis runs), and source-reliability weighting.
"""
from agents import intake_agent, analysis_agent, risk_agent, resource_agent, hospital_agent, planning_agent, knowledge_base

SOURCE_RELIABILITY = {
    "FIELD_OFFICER": "HIGH",
    "VERIFIED_ORG": "HIGH",
    "EMERGENCY_OPERATOR": "HIGH",
    "CITIZEN": "MEDIUM",
    "SOCIAL_MEDIA": "LOW",
}


def reliability_for_source(source_type: str) -> str:
    return SOURCE_RELIABILITY.get(source_type.upper(), "MEDIUM")


def detect_conflicts(reports):
    """
    reports: list of IncidentReport ORM objects (already persisted) with
    extracted_victims populated where possible.
    Returns (conflicting: bool, notes: str, victim_min, victim_max)
    """
    victim_numbers = [r.extracted_victims for r in reports if r.extracted_victims is not None]
    if len(victim_numbers) < 2:
        vmin = min(victim_numbers) if victim_numbers else None
        vmax = max(victim_numbers) if victim_numbers else None
        return False, None, vmin, vmax

    vmin, vmax = min(victim_numbers), max(victim_numbers)
    # Conflict if the spread is large relative to the estimate itself
    spread = vmax - vmin
    conflicting = spread > 0 and (spread >= 3 or (vmax > 0 and spread / vmax > 0.4))

    notes = None
    if conflicting:
        notes = (
            f"Reports disagree on affected-person count (range {vmin}-{vmax} across {len(victim_numbers)} reports). "
            f"Treating as a range rather than a single figure until field-verified."
        )
    return conflicting, notes, vmin, vmax


def run_full_pipeline(incident, reports, available_resources, hospitals):
    """
    incident: Incident ORM object (already has hazards/type/location set from intake)
    reports: list of IncidentReport ORM objects for this incident
    available_resources: list of Resource ORM objects with status == AVAILABLE
    hospitals: list of Hospital ORM objects
    """
    analysis = analysis_agent.run_analysis(
        incident_type=incident.incident_type,
        hazards=incident.hazards or [],
        victim_min=incident.estimated_victims_min,
        victim_max=incident.estimated_victims_max,
        conflicting_info=incident.conflicting_info,
    )

    risk_assessment = risk_agent.assess_risks(incident.incident_type, incident.hazards or [])

    resource_alloc = resource_agent.allocate_resources(
        incident_type=incident.incident_type,
        severity=analysis["severity"],
        incident_lat=incident.latitude,
        incident_lon=incident.longitude,
        available_resources=available_resources,
    )

    hospital_rec = hospital_agent.recommend_hospitals(
        incident_lat=incident.latitude,
        incident_lon=incident.longitude,
        severity=analysis["severity"],
        estimated_victims=incident.estimated_victims_max or 0,
        hospitals=hospitals,
    )

    kb_snippets = knowledge_base.retrieve(incident.incident_type, severity=analysis["severity"])

    plan = planning_agent.build_response_plan(
        incident=incident,
        analysis=analysis,
        resource_alloc=resource_alloc,
        hospital_rec=hospital_rec,
        risk_assessment=risk_assessment,
        kb_snippets=kb_snippets,
    )

    return {
        "analysis": analysis,
        "risk_assessment": risk_assessment,
        "resource_alloc": resource_alloc,
        "hospital_rec": hospital_rec,
        "plan": plan,
    }
