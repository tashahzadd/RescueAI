"""
AGENT 2: Situation Analysis Agent

Determines severity/urgency from the structured incident produced by the
Intake Agent, plus the (possibly conflicting) set of reports received so far.
Always returns an explanation for the severity classification, and flags
information gaps that a human should chase down.
"""

HIGH_SEVERITY_TYPES = {"Building Collapse", "Earthquake", "Industrial Accident"}
MEDIUM_SEVERITY_TYPES = {"Fire", "Flood", "Landslide"}

CRITICAL_HAZARDS = {"Fire", "Structural instability", "Gas leakage", "Trapped victims"}


def run_analysis(incident_type: str, hazards: list, victim_min, victim_max, conflicting_info: bool):
    reasons = []
    score = 0

    if incident_type in HIGH_SEVERITY_TYPES:
        score += 3
        reasons.append(f"{incident_type} incidents carry inherently high risk to life and structures.")
    elif incident_type in MEDIUM_SEVERITY_TYPES:
        score += 2
        reasons.append(f"{incident_type} incidents typically require an urgent, multi-unit response.")
    else:
        score += 1

    hazard_hits = [h for h in hazards if h in CRITICAL_HAZARDS]
    if hazard_hits:
        score += len(hazard_hits)
        reasons.append(f"Critical hazard(s) present: {', '.join(hazard_hits)}.")

    victims = victim_max or victim_min or 0
    if victims >= 10:
        score += 3
        reasons.append(f"Potentially large number of people affected (up to {victims}).")
    elif victims >= 1:
        score += 1
        reasons.append(f"At least {victims} person(s) reported affected.")

    if "Trapped victims" in hazards:
        score += 2
        reasons.append("Reports indicate trapped victims, raising urgency.")

    if conflicting_info:
        reasons.append("Conflicting victim counts across reports increase uncertainty and warrant a cautious (higher) severity until verified.")
        score += 1

    if score >= 8:
        severity = "CRITICAL"
    elif score >= 5:
        severity = "HIGH"
    elif score >= 3:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    information_gaps = []
    if victim_min is None and victim_max is None:
        information_gaps.append("No victim count reported - field verification needed.")
    if not hazards:
        information_gaps.append("No hazards explicitly reported - confirm scene conditions.")
    if conflicting_info:
        information_gaps.append("Victim estimates conflict across sources - request field verification.")

    severity_confidence = 0.95 if not conflicting_info else 0.65

    return {
        "severity": severity,
        "severity_score": score,
        "reasons": reasons,
        "information_gaps": information_gaps,
        "confidence": {"severity": round(severity_confidence, 2)},
    }
