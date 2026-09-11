
"""
AGENT 3: Resource Allocation Agent

Geographically-aware emergency resource allocation for RescueAI.

Priority:
1. Suitable resources very close to the incident
2. Nearby city/district resources
3. Regional/provincial fallback
4. Long-distance mutual aid only when necessary

All recommendations remain decision-support only and require
human approval before dispatch.
"""

import math


# Exact incident names used by the national demo dataset
INCIDENT_RESOURCE_REQUIREMENTS = {

    "Flood": [
        "Rescue Team",
        "Water Tanker",
        "Shelter Unit",
        "Medical Team",
    ],

    "Flood Emergency": [
        "Rescue Team",
        "Water Tanker",
        "Shelter Unit",
        "Medical Team",
    ],

    "Earthquake": [
        "Search & Rescue Team",
        "Heavy Rescue Equipment",
        "Ambulance",
        "Medical Team",
    ],

    "Fire": [
        "Fire Unit",
        "Ambulance",
        "Medical Team",
    ],

    "Electrical Fire": [
        "Fire Unit",
        "Utility Team",
        "Ambulance",
        "Medical Team",
    ],

    "Road Accident": [
        "Ambulance",
        "Fire Unit",
        "Rescue Team",
    ],

    "Road Traffic Accident": [
        "Ambulance",
        "Fire Unit",
        "Rescue Team",
    ],

    "Building Collapse": [
        "Search & Rescue Team",
        "Heavy Rescue Equipment",
        "Ambulance",
        "Fire Unit",
        "Medical Team",
    ],

    "Medical Emergency": [
        "Ambulance",
        "Medical Team",
    ],

    "Heatwave": [
        "Medical Team",
        "Water Tanker",
        "Shelter Unit",
    ],

    "Heatwave Emergency": [
        "Medical Team",
        "Water Tanker",
        "Shelter Unit",
    ],

    "Landslide": [
        "Search & Rescue Team",
        "Heavy Rescue Equipment",
        "Rescue Team",
        "Ambulance",
    ],

    "Industrial Accident": [
        "Fire Unit",
        "Medical Team",
        "Utility Team",
        "Ambulance",
    ],

    "Gas Leak": [
        "Fire Unit",
        "Utility Team",
        "Ambulance",
        "Medical Team",
    ],

    "Water Rescue": [
        "Rescue Team",
        "Ambulance",
        "Medical Team",
    ],

    "Urban Search and Rescue": [
        "Search & Rescue Team",
        "Heavy Rescue Equipment",
        "Ambulance",
    ],

    "Other": [
        "Rescue Team",
        "Ambulance",
    ],
}


SEVERITY_MULTIPLIER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


def _haversine_km(lat1, lon1, lat2, lon2):
    """
    Calculate straight-line geographic distance in kilometers.
    """

    if None in (lat1, lon1, lat2, lon2):
        return 9999.0

    R = 6371.0

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.asin(math.sqrt(a))

    return R * c


def required_resource_types(incident_type: str) -> list:
    """
    Return resource types required for the incident.

    Exact match is tried first. Then a few keyword-based fallbacks
    are used so slightly different frontend labels do not break
    allocation.
    """

    if incident_type in INCIDENT_RESOURCE_REQUIREMENTS:
        return INCIDENT_RESOURCE_REQUIREMENTS[incident_type]

    text = (incident_type or "").lower()

    if "collapse" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Building Collapse"]

    if "traffic" in text or "road" in text or "accident" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Road Traffic Accident"]

    if "electrical" in text and "fire" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Electrical Fire"]

    if "fire" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Fire"]

    if "flood" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Flood Emergency"]

    if "heat" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Heatwave Emergency"]

    if "landslide" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Landslide"]

    if "gas" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Gas Leak"]

    if "water rescue" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Water Rescue"]

    if "medical" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Medical Emergency"]

    if "industrial" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Industrial Accident"]

    if "search" in text and "rescue" in text:
        return INCIDENT_RESOURCE_REQUIREMENTS["Urban Search and Rescue"]

    return INCIDENT_RESOURCE_REQUIREMENTS["Other"]


def _distance_tier(distance):
    """
    Geographic priority tier.

    Lower tier is better.

    Tier 0: local / same urban area
    Tier 1: nearby city or district
    Tier 2: regional/provincial support
    Tier 3: distant mutual aid
    Tier 4: extreme distance
    """

    if distance <= 30:
        return 0

    if distance <= 100:
        return 1

    if distance <= 250:
        return 2

    if distance <= 500:
        return 3

    return 4


def score_resource(resource, incident_lat, incident_lon):
    """
    Lower score = better.

    Geographic priority is intentionally dominant.

    A nearby available resource should normally beat a very distant
    resource, even if the distant resource has slightly more workload
    headroom.
    """

    distance = _haversine_km(
        incident_lat,
        incident_lon,
        resource.latitude,
        resource.longitude,
    )

    capacity = resource.capacity or 1
    workload = resource.current_workload or 0

    workload_ratio = min(workload / capacity, 1.0)

    tier = _distance_tier(distance)

    # Large tier penalty prevents Karachi from beating Rawalpindi
    # when appropriate local resources exist.
    tier_penalty = tier * 1000

    # Distance remains important within each geographic tier.
    distance_penalty = distance

    # Workload is important but should not outweigh geography.
    workload_penalty = workload_ratio * 25

    score = (
        tier_penalty
        + distance_penalty
        + workload_penalty
    )

    return score, {
        "distance_km": round(distance, 2),
        "distance_tier": tier,
        "workload_ratio": round(workload_ratio, 2),
    }


def allocate_resources(
    incident_type: str,
    severity: str,
    incident_lat,
    incident_lon,
    available_resources: list,
    top_n_per_type: int = 1,
):
    """
    available_resources:
        Resource ORM objects whose status is AVAILABLE.

    Returns:
        Resource recommendations grouped by required resource type.
    """

    needed_types = required_resource_types(incident_type)

    severity = (severity or "LOW").upper()

    multiplier = SEVERITY_MULTIPLIER.get(
        severity,
        1,
    )

    recommendations = []

    for r_type in needed_types:

        candidates = [
            r
            for r in available_resources
            if r.resource_type == r_type
        ]

        scored = []

        for resource in candidates:

            score, factors = score_resource(
                resource,
                incident_lat,
                incident_lon,
            )

            scored.append(
                (
                    score,
                    resource,
                    factors,
                )
            )

        scored.sort(
            key=lambda x: (
                x[2]["distance_tier"],
                x[0],
            )
        )

        # Medium/low: normally one unit.
        # High/critical: normally two units where available.
        number_required = max(
            1,
            top_n_per_type,
        )

        if severity in ("HIGH", "CRITICAL"):
            number_required += 1

        chosen = scored[:min(
            len(scored),
            number_required,
        )]

        recommendations.append(
            {
                "resource_type": r_type,

                "candidates_considered": len(
                    candidates
                ),

                "chosen": [
                    {
                        "id": resource.id,
                        "name": resource.name,
                        "organization": resource.organization,

                        "distance_km":
                            factors["distance_km"],

                        "distance_tier":
                            factors["distance_tier"],

                        "workload_ratio":
                            factors["workload_ratio"],

                        "reason": (
                            f"Geographically prioritized "
                            f"{factors['distance_km']} km from "
                            f"incident; geographic tier "
                            f"{factors['distance_tier']}; "
                            f"{int(factors['workload_ratio'] * 100)}% "
                            f"current workload; suitable "
                            f"{r_type} for {incident_type}."
                        ),
                    }

                    for score, resource, factors
                    in chosen
                ],

                "gap": (
                    None
                    if chosen
                    else
                    f"No available {r_type} found - "
                    f"request regional mutual aid."
                ),
            }
        )

    confidence = (
        0.90
        if all(
            rec["chosen"]
            for rec in recommendations
        )
        else 0.60
    )

    return {
        "recommendations": recommendations,
        "severity_multiplier_applied": multiplier,
        "confidence": {
            "resource_recommendation": confidence
        },
    }
