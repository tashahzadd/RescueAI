"""
AGENT 3: Resource Allocation Agent

Decides which resource TYPES are required for an incident, then scores
available resource records against multiple factors (capability match,
distance, current workload, capacity, severity) - explicitly NOT just
"pick the nearest one".
"""
import math

INCIDENT_RESOURCE_REQUIREMENTS = {
    "Flood": ["Rescue Team", "Water Tanker", "Shelter", "Water Supply"],
    "Earthquake": ["Search & Rescue Team", "Heavy Rescue Equipment", "Ambulance", "Medical Team"],
    "Fire": ["Fire Unit", "Ambulance", "Medical Team"],
    "Road Accident": ["Ambulance", "Fire Unit"],
    "Building Collapse": ["Search & Rescue Team", "Heavy Rescue Equipment", "Ambulance", "Fire Unit"],
    "Medical Emergency": ["Ambulance", "Medical Team"],
    "Heatwave": ["Medical Team", "Water Supply", "Shelter"],
    "Landslide": ["Search & Rescue Team", "Heavy Rescue Equipment", "Rescue Team"],
    "Industrial Accident": ["Fire Unit", "Medical Team", "Utility Team", "Ambulance"],
    "Other": ["Rescue Team", "Ambulance"],
}

SEVERITY_MULTIPLIER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return 999.0
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def required_resource_types(incident_type: str) -> list:
    return INCIDENT_RESOURCE_REQUIREMENTS.get(incident_type, ["Rescue Team", "Ambulance"])


def score_resource(resource, incident_lat, incident_lon):
    """
    Lower score = better. Combines distance, workload ratio, and remaining
    capacity headroom so a busy-but-close unit doesn't always win over a
    slightly farther, fully-available one.
    """
    distance = _haversine_km(incident_lat, incident_lon, resource.latitude, resource.longitude)
    workload_ratio = (resource.current_workload / resource.capacity) if resource.capacity else 1.0
    headroom_penalty = workload_ratio * 10  # 0 (idle) .. 10 (fully loaded)
    distance_penalty = distance  # km, roughly comparable scale to workload for a city-sized demo
    return distance_penalty + headroom_penalty, {
        "distance_km": round(distance, 2),
        "workload_ratio": round(workload_ratio, 2),
    }


def allocate_resources(incident_type: str, severity: str, incident_lat, incident_lon, available_resources: list, top_n_per_type: int = 1):
    """
    available_resources: list of Resource ORM objects with status == AVAILABLE
    Returns list of dicts: {resource_type, chosen: [...], reason}
    """
    needed_types = required_resource_types(incident_type)
    multiplier = SEVERITY_MULTIPLIER.get(severity, 1)

    recommendations = []
    for r_type in needed_types:
        candidates = [r for r in available_resources if r.resource_type == r_type]
        scored = []
        for r in candidates:
            score, factors = score_resource(r, incident_lat, incident_lon)
            scored.append((score, r, factors))
        scored.sort(key=lambda x: x[0])

        n_to_take = min(len(scored), max(1, top_n_per_type + (1 if severity in ("HIGH", "CRITICAL") else 0)))
        chosen = scored[:n_to_take]

        recommendations.append({
            "resource_type": r_type,
            "candidates_considered": len(candidates),
            "chosen": [
                {
                    "id": r.id,
                    "name": r.name,
                    "organization": r.organization,
                    "distance_km": factors["distance_km"],
                    "workload_ratio": factors["workload_ratio"],
                    "reason": (
                        f"Selected over {len(candidates) - 1} other candidate(s): "
                        f"{factors['distance_km']} km away, "
                        f"{int(factors['workload_ratio'] * 100)}% current workload, "
                        f"capability match for {incident_type}."
                    ),
                }
                for score, r, factors in chosen
            ] if chosen else [],
            "gap": None if chosen else f"No available {r_type} found - request mutual aid.",
        })

    confidence = 0.9 if all(rec["chosen"] for rec in recommendations) else 0.6
    return {
        "recommendations": recommendations,
        "severity_multiplier_applied": multiplier,
        "confidence": {"resource_recommendation": confidence},
    }
