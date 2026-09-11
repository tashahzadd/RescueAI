"""
AGENT 1: Emergency Intake Agent

Turns raw free-text emergency reports into structured incident data:
incident type, victim estimate, hazards, and extracted entities.

Implemented as transparent rule/keyword extraction rather than an opaque
model call, so every field can be traced back to the text that produced it -
this keeps the system explainable and works with or without an LLM_API_KEY.
If an LLM_API_KEY is configured, `classify()` can be swapped to call out to
it; the structured-output contract stays identical.
"""
import re

INCIDENT_KEYWORDS = {
    "Flood": ["flood", "flooding", "inundat", "water level", "overflow"],
    "Earthquake": ["earthquake", "tremor", "seismic", "quake"],
    "Fire": ["fire", "blaze", "burning", "smoke", "flames"],
    "Road Accident": ["accident", "collision", "crash", "overturned", "vehicle"],
    "Building Collapse": ["collapse", "collapsed", "caved in", "structure fell", "rubble"],
    "Medical Emergency": ["cardiac", "unconscious", "medical emergency", "overdose", "seizure"],
    "Heatwave": ["heatwave", "heat wave", "heatstroke", "extreme heat"],
    "Landslide": ["landslide", "mudslide", "slope failure"],
    "Industrial Accident": ["chemical leak", "explosion", "industrial", "factory", "gas leak"],
}

HAZARD_KEYWORDS = {
    "Fire": ["fire", "smoke", "flames", "burning"],
    "Structural instability": ["collapse", "unstable", "cracked", "caved"],
    "Gas leakage": ["gas leak", "gas smell", "explosion risk"],
    "Electrical hazard": ["electrical", "power line", "live wire", "downed line"],
    "Flooding": ["flood", "water level", "submerged"],
    "Trapped victims": ["trapped", "stuck", "buried"],
}

VICTIM_PATTERN = re.compile(r"(\d+)\s*(?:\+|plus)?\s*(?:people|persons|victims|individuals|residents)?", re.IGNORECASE)


def _detect_incident_type(text: str):
    text_lower = text.lower()
    scores = {}
    for incident_type, keywords in INCIDENT_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in text_lower]
        if hits:
            scores[incident_type] = hits
    if not scores:
        return "Other", [], 0.4
    best_type = max(scores, key=lambda k: len(scores[k]))
    confidence = min(0.99, 0.7 + 0.1 * len(scores[best_type]))
    return best_type, scores[best_type], confidence


def _detect_hazards(text: str):
    text_lower = text.lower()
    hazards = []
    for hazard, keywords in HAZARD_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            hazards.append(hazard)
    return hazards


def _extract_victim_estimate(text: str):
    matches = re.findall(r"(\d+)", text)
    if not matches:
        return None, None, []
    numbers = [int(m) for m in matches]
    return min(numbers), max(numbers), numbers


def run_intake(raw_text: str, location: str = None, latitude: float = None,
               longitude: float = None, source_type: str = "CITIZEN"):
    incident_type, matched_keywords, type_confidence = _detect_incident_type(raw_text)
    hazards = _detect_hazards(raw_text)
    victim_min, victim_max, raw_numbers = _extract_victim_estimate(raw_text)

    entities = {
        "matched_keywords": matched_keywords,
        "raw_numbers_found": raw_numbers,
        "mentions_smoke": "smoke" in raw_text.lower(),
        "mentions_trapped": "trapped" in raw_text.lower(),
    }

    result = {
        "incident_type": incident_type,
        "location": location or "Unknown - requires field confirmation",
        "latitude": latitude,
        "longitude": longitude,
        "estimated_victims_min": victim_min,
        "estimated_victims_max": victim_max,
        "hazards": hazards,
        "entities": entities,
        "confidence": {"incident_classification": round(type_confidence, 2)},
        "explainability": {
            "incident_type_reason": (
                f"Matched keyword(s): {', '.join(matched_keywords)}" if matched_keywords
                else "No strong keyword match; defaulted to 'Other' pending review."
            ),
        },
    }
    return result
