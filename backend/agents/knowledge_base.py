"""
Lightweight RAG module.

For the hackathon MVP this uses transparent keyword/category matching rather
than a vector database - it's fast, has zero external dependencies, and (most
importantly for an explainable system) makes it obvious *why* a given guidance
snippet was retrieved. Swapping in a real embedding index later is a drop-in
replacement: only `retrieve()` needs to change.
"""
import os

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")

# Maps incident_type -> knowledge base filename
INCIDENT_TO_DOC = {
    "Flood": "flood_response.md",
    "Fire": "fire_response.md",
    "Earthquake": "earthquake_response.md",
    "Building Collapse": "building_collapse.md",
    "Road Accident": "road_accident.md",
    "Heatwave": "heatwave.md",
    "Industrial Accident": "fire_response.md",
    "Landslide": "earthquake_response.md",
    "Medical Emergency": "mass_casualty.md",
    "Other": "evacuation.md",
}

_cache = {}


def _load(doc_name: str) -> str:
    if doc_name not in _cache:
        path = os.path.join(KB_DIR, doc_name)
        try:
            with open(path, "r") as f:
                _cache[doc_name] = f.read()
        except FileNotFoundError:
            _cache[doc_name] = ""
    return _cache[doc_name]


def retrieve(incident_type: str, severity: str = None, extra_docs: list = None):
    """
    Return a list of {source, bullets} guidance snippets relevant to the
    incident type (and mass-casualty guidance too, if severity is CRITICAL).
    """
    docs_to_fetch = []
    primary_doc = INCIDENT_TO_DOC.get(incident_type, "evacuation.md")
    docs_to_fetch.append(primary_doc)

    if severity == "CRITICAL" and "mass_casualty.md" not in docs_to_fetch:
        docs_to_fetch.append("mass_casualty.md")

    if extra_docs:
        for d in extra_docs:
            if d not in docs_to_fetch:
                docs_to_fetch.append(d)

    results = []
    for doc in docs_to_fetch:
        content = _load(doc)
        if not content:
            continue
        bullets = [
            line.strip("- ").strip()
            for line in content.splitlines()
            if line.strip().startswith("-")
        ]
        results.append({"source": doc, "bullets": bullets})
    return results
