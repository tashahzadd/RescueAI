"""
AGENT 6: Response Planning Agent

Combines the outputs of the other five agents into a single explainable
response plan. This plan is what gets shown to the human decision-maker for
APPROVE / MODIFY / REJECT - the AI never dispatches anything itself.
"""

BASE_ACTION_SEQUENCE = {
    "Building Collapse": [
        "Dispatch Search & Rescue team to the site",
        "Dispatch ambulance(s) for triage and transport",
        "Dispatch fire unit as precaution against secondary fire",
        "Notify recommended hospital of incoming casualties",
        "Establish a safety perimeter around the structure",
        "Request utility isolation (gas/electric) before entry",
        "Prepare additional medical support on standby",
    ],
    "Fire": [
        "Dispatch fire unit(s) to the scene",
        "Dispatch ambulance(s) for smoke-inhalation/injury triage",
        "Establish a safety perimeter",
        "Request utility isolation near the fire zone",
        "Notify recommended hospital",
    ],
    "Flood": [
        "Dispatch rescue team with flood-rescue equipment",
        "Dispatch water tanker / shelter support for displaced residents",
        "Isolate electrical supply in affected area if possible",
        "Notify recommended hospital and shelter locations",
        "Coordinate with utility team on road-blockage clearance",
    ],
    "Earthquake": [
        "Dispatch Search & Rescue team(s) with heavy rescue equipment",
        "Dispatch ambulance(s) and medical team(s)",
        "Establish a safety perimeter accounting for aftershock risk",
        "Notify recommended hospital and prepare mass-casualty protocol",
    ],
    "Road Accident": [
        "Dispatch ambulance to the scene",
        "Dispatch fire unit for extrication/fire-risk mitigation",
        "Establish traffic control around the scene",
        "Notify recommended hospital",
    ],
}

DEFAULT_ACTION_SEQUENCE = [
    "Dispatch appropriate rescue/medical resources to the scene",
    "Establish a safety perimeter",
    "Notify recommended hospital",
    "Request field verification of unresolved details",
]


def build_response_plan(incident, analysis, resource_alloc, hospital_rec, risk_assessment, kb_snippets):
    incident_type = incident.incident_type
    severity = analysis["severity"]

    actions = list(BASE_ACTION_SEQUENCE.get(incident_type, DEFAULT_ACTION_SEQUENCE))
    if incident.conflicting_info:
        actions.append("Request field verification to resolve conflicting victim counts before full resource commitment")

    victims_desc = (
        f"{incident.estimated_victims_min}-{incident.estimated_victims_max}"
        if incident.estimated_victims_min != incident.estimated_victims_max
        else str(incident.estimated_victims_max or "unknown")
    )

    summary = (
        f"{incident_type} at {incident.location}. Estimated {victims_desc} person(s) affected. "
        f"Severity assessed as {severity}. "
        f"{'Recommended hospital: ' + hospital_rec['recommended']['name'] + '. ' if hospital_rec.get('recommended') else ''}"
        f"This is an AI-generated recommendation requiring human approval before any dispatch."
    )

    information_gaps = list(analysis.get("information_gaps", []))
    for rec in resource_alloc["recommendations"]:
        if rec.get("gap"):
            information_gaps.append(rec["gap"])
    if hospital_rec.get("gap"):
        information_gaps.append(hospital_rec["gap"])
    # Note: hospital_rec["capacity_caveat"] is surfaced directly next to the
    # hospital recommendation in the UI rather than duplicated here.

    kb_refs = [snip["source"] for snip in kb_snippets]

    confidence = {
        "incident_classification": incident.confidence.get("incident_classification"),
        "severity": analysis["confidence"]["severity"],
        "victim_estimate": 0.65 if incident.conflicting_info else 0.85,
        "resource_recommendation": resource_alloc["confidence"]["resource_recommendation"],
        "hospital_recommendation": hospital_rec["confidence"]["hospital_recommendation"],
    }

    explainability = {
        "severity_reasons": analysis["reasons"],
        "risk_reasoning": risk_assessment["reasoning"],
        "resource_reasoning": [
            {"resource_type": r["resource_type"], "picks": [c["reason"] for c in r["chosen"]]}
            for r in resource_alloc["recommendations"]
        ],
        "hospital_reasoning": hospital_rec.get("recommended", {}).get("reason"),
        "knowledge_base_guidance": {snip["source"]: snip["bullets"] for snip in kb_snippets},
    }

    return {
        "summary": summary,
        "severity": severity,
        "recommended_resources": resource_alloc["recommendations"],
        "recommended_hospital": hospital_rec,
        "risks": risk_assessment["risks"],
        "actions": actions,
        "information_gaps": list(dict.fromkeys(information_gaps)),
        "knowledge_base_refs": kb_refs,
        "confidence": confidence,
        "explainability": explainability,
    }
