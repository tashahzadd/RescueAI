"""
AGENT 1: Emergency Intake Agent

Turns raw free-text emergency reports into structured incident data:
incident type, victim estimate, hazards, location, and extracted entities.

Uses transparent rule/keyword extraction so each result remains explainable.
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


# Demo city centroids used only when exact GPS coordinates are not provided.
CITY_COORDINATES = {
    "karachi": (24.8607, 67.0011),
    "hyderabad": (25.3960, 68.3578),
    "sukkur": (27.7244, 68.8228),
    "larkana": (27.5590, 68.2123),
    "nawabshah": (26.2442, 68.4100),
    "mirpur khas": (25.5269, 69.0110),

    "lahore": (31.5497, 74.3436),
    "rawalpindi": (33.5651, 73.0169),
    "faisalabad": (31.4504, 73.1350),
    "multan": (30.1575, 71.5249),
    "gujranwala": (32.1877, 74.1945),
    "sialkot": (32.4945, 74.5229),
    "bahawalpur": (29.3956, 71.6836),
    "sargodha": (32.0836, 72.6711),
    "dera ghazi khan": (30.0561, 70.6348),

    "peshawar": (34.0151, 71.5249),
    "mardan": (34.1989, 72.0231),
    "abbottabad": (34.1688, 73.2215),
    "swat": (35.2227, 72.4258),
    "kohat": (33.5819, 71.4497),
    "dera ismail khan": (31.8315, 70.9017),

    "quetta": (30.1798, 66.9750),
    "gwadar": (25.1264, 62.3225),
    "turbat": (26.0023, 63.0600),
    "khuzdar": (27.8000, 66.6167),

    "islamabad": (33.6844, 73.0479),
    "muzaffarabad": (34.3700, 73.4711),
    "gilgit": (35.9208, 74.3086),
    "skardu": (35.2971, 75.6333),
}


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

    confidence = min(
        0.99,
        0.7 + 0.1 * len(scores[best_type])
    )

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


def _resolve_location_coordinates(location: str):
    """
    Resolve a known demo city from a location string.

    Example:
        "Lalazar, Rawalpindi" -> Rawalpindi coordinates
        "Gulberg, Lahore" -> Lahore coordinates

    Returns:
        latitude, longitude, matched_city
    """

    if not location:
        return None, None, None

    location_lower = location.lower()

    # Longest names first so multi-word cities are matched safely.
    sorted_cities = sorted(
        CITY_COORDINATES.keys(),
        key=len,
        reverse=True
    )

    for city in sorted_cities:
        if city in location_lower:
            latitude, longitude = CITY_COORDINATES[city]

            return latitude, longitude, city.title()

    return None, None, None


def run_intake(
    raw_text: str,
    location: str = None,
    latitude: float = None,
    longitude: float = None,
    source_type: str = "CITIZEN",
):
    incident_type, matched_keywords, type_confidence = _detect_incident_type(raw_text)

    hazards = _detect_hazards(raw_text)

    victim_min, victim_max, raw_numbers = _extract_victim_estimate(raw_text)

    resolved_city = None
    coordinate_source = "UNKNOWN"

    # Priority 1:
    # Exact coordinates supplied by caller/device.
    if latitude is not None and longitude is not None:
        resolved_latitude = latitude
        resolved_longitude = longitude
        coordinate_source = "PROVIDED_GPS"

    else:
        # Priority 2:
        # Resolve coordinates from city named in location.
        (
            resolved_latitude,
            resolved_longitude,
            resolved_city,
        ) = _resolve_location_coordinates(location)

        if resolved_latitude is not None:
            coordinate_source = "CITY_CENTROID"

        else:
            # Priority 3:
            # Do not invent coordinates.
            resolved_latitude = None
            resolved_longitude = None


    entities = {
        "matched_keywords": matched_keywords,
        "raw_numbers_found": raw_numbers,
        "mentions_smoke": "smoke" in raw_text.lower(),
        "mentions_trapped": "trapped" in raw_text.lower(),
        "resolved_city": resolved_city,
        "coordinate_source": coordinate_source,
    }


    result = {
        "incident_type": incident_type,

        "location": location or "Unknown - requires field confirmation",

        "latitude": resolved_latitude,

        "longitude": resolved_longitude,

        "estimated_victims_min": victim_min,

        "estimated_victims_max": victim_max,

        "hazards": hazards,

        "entities": entities,

        "confidence": {
            "incident_classification": round(type_confidence, 2)
        },

        "explainability": {
            "incident_type_reason": (
                f"Matched keyword(s): {', '.join(matched_keywords)}"
                if matched_keywords
                else "No strong keyword match; defaulted to 'Other' pending review."
            ),

            "location_reason": (
                f"Exact coordinates supplied directly."
                if coordinate_source == "PROVIDED_GPS"
                else
                f"Location matched to {resolved_city} demo city centroid."
                if coordinate_source == "CITY_CENTROID"
                else
                "Location could not be converted to coordinates and requires verification."
            ),
        },
    }

    return result
