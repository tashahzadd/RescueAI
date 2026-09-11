"""
Seeds the database from the synthetic demo datasets in backend/data/.

IMPORTANT: everything loaded here is clearly-labeled DUMMY/DEMO data (see
backend/data/SOURCES.md for the full explanation and the real-data roadmap).
No live or scraped government data is used - this environment has no
network access, and fabricating "real" numbers would be dishonest.

Safe to re-run - it only seeds empty tables unless --full-reset is passed.
"""
import csv
import os
import sys

from database import Base, engine, SessionLocal
import models

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

USERS = [
    {"name": "Amir Khan", "email": "amir.commander@demo.rescueai", "role": "COMMANDER"},
    {"name": "Sana Malik", "email": "sana.dispatcher@demo.rescueai", "role": "DISPATCHER"},
    {"name": "Bilal Ahmed", "email": "bilal.admin@demo.rescueai", "role": "ADMIN"},
    {"name": "Ayesha Raza", "email": "ayesha.field@demo.rescueai", "role": "FIELD_RESPONDER"},
    {"name": "Dr. Farooq", "email": "farooq.hospital@demo.rescueai", "role": "HOSPITAL_COORDINATOR"},
    {"name": "Guest Viewer", "email": "guest.viewer@demo.rescueai", "role": "VIEWER"},
]


def _read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_hospitals_from_csv(filename):
    hospitals = []
    for row in _read_csv(filename):
        hospitals.append(models.Hospital(
            name=row["name"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            emergency_beds=int(row["emergency_beds"]),
            icu_beds=int(row["icu_beds"]),
            trauma_capacity=row["trauma_capacity"],
            current_load=int(round(0.3 * int(row["emergency_beds"]))),  # synthetic starting load ~30%
            status=row["status"],
            district=row["district"],
            facility_type=row["facility_type"],
            ownership=row["ownership"],
            source_name=row["source_name"],
            source_url=row["source_url"],
            trust_level=row["trust_level"],
            last_verified=row["last_verified"],
        ))
    return hospitals


def _load_resources_from_csv(filename):
    resources = []
    for row in _read_csv(filename):
        capabilities = [c for c in row["capabilities"].split("|") if c] if row["capabilities"] else []
        equipment = [e for e in row["equipment"].split("|") if e] if row["equipment"] else []
        resources.append(models.Resource(
            name=row["name"],
            resource_type=row["resource_type"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            capabilities=capabilities,
            equipment=equipment,
            capacity=int(row["capacity"]),
            organization=row["organization"],
            trust_level=row["trust_level"],
        ))
    return resources


def seed(full_reset: bool = False):
    if full_reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.Resource).count() == 0:
            resources = _load_resources_from_csv("resources_demo.csv")
            db.add_all(resources)
            print(f"Loaded {len(resources)} resources from resources_demo.csv (all trust_level=DEMO)")

        if db.query(models.Hospital).count() == 0:
            hospitals = (
                _load_hospitals_from_csv("hospitals_sindh_demo.csv")
                + _load_hospitals_from_csv("hospitals_punjab_demo.csv")
            )
            db.add_all(hospitals)
            print(f"Loaded {len(hospitals)} hospitals from hospitals_sindh_demo.csv + hospitals_punjab_demo.csv (all trust_level=DEMO)")

        if db.query(models.User).count() == 0:
            for u in USERS:
                db.add(models.User(**u))
            print(f"Loaded {len(USERS)} demo users")

        db.commit()
        print("Seed complete. See backend/data/SOURCES.md for data provenance notes.")
    finally:
        db.close()


if __name__ == "__main__":
    seed(full_reset="--full-reset" in sys.argv)
