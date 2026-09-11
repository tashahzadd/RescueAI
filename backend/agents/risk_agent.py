"""
AGENT 5: Risk Assessment Agent

Identifies secondary/downstream risks based on incident type and observed
hazards, drawing on the same categories referenced in the RAG knowledge base.
"""

SECONDARY_RISKS = {
    "Building Collapse": ["Structural instability", "Gas leakage", "Electrical hazards", "Fire", "Secondary collapse"],
    "Earthquake": ["Structural instability", "Aftershocks", "Gas leakage", "Electrical hazards", "Mass casualties"],
    "Flood": ["Electrical hazards", "Contaminated water", "Disease risk", "Road blockage", "Isolation of communities"],
    "Fire": ["Structural weakening", "Smoke inhalation", "Secondary explosions", "Electrical hazards"],
    "Landslide": ["Secondary slides", "Road blockage", "Structural damage", "Isolation of communities"],
    "Industrial Accident": ["Chemical exposure", "Explosion risk", "Air quality hazard", "Fire"],
    "Road Accident": ["Fuel leakage/fire risk", "Secondary collisions", "Traffic congestion blocking access"],
    "Heatwave": ["Heatstroke", "Dehydration", "Power grid strain"],
    "Medical Emergency": ["Delayed treatment risk", "Crowd control at scene"],
    "Other": ["Unknown scene hazards - request field assessment"],
}


def assess_risks(incident_type: str, hazards: list):
    base_risks = SECONDARY_RISKS.get(incident_type, SECONDARY_RISKS["Other"])
    # Merge with directly-observed hazards (deduplicated, observed first)
    combined = list(dict.fromkeys(hazards + base_risks))
    return {
        "risks": combined,
        "reasoning": f"Derived from known secondary-risk patterns for {incident_type}, combined with hazards directly reported at the scene.",
        "confidence": {"risk_assessment": 0.85},
    }
