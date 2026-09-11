# Data Sources & Provenance — READ THIS BEFORE PRESENTING TO JUDGES

## What the data in this repo actually is

Every hospital, resource, and statistic in `backend/data/*.csv` is
**synthetic demo data**, hand-authored for this hackathon MVP. Facility
names are marked `(DEMO)`, `trust_level` is `DEMO` everywhere, and
`source_url` says `N/A - dummy data`.

**Nothing here was scraped or pulled from a live government source.** This
project was built in a network-isolated environment with no ability to
fetch external URLs, so it would have been dishonest to present fabricated
numbers as if they came from the Sindh Health Department, Punjab Health
Department, SHCC, or Rescue 1122. Instead, the CSVs are *structured the way
those real datasets are structured* (same kind of fields: district, taluka/
tehsil, facility type, bed counts, ownership, operational status), so that
swapping in the real thing later is a data-loading change, not a redesign.

## The trust-level / provenance model this schema supports

Following the research you did into real Pakistani sources, every
`Hospital` and `Resource` record now carries:

| Field | Meaning |
|---|---|
| `source_name` | Who/what this data came from |
| `source_url` | Link to the source, if any |
| `trust_level` | `OFFICIAL` (government dataset), `LIVE` (a hospital's own real-time feed), `REPORTED` (manually updated by a human), `PUBLIC` (crowd-sourced/OSM-style), or `DEMO` (synthetic, this repo's default) |
| `last_verified` | When the figure was last confirmed |

The AI **surfaces this**: when a hospital's `trust_level` isn't `LIVE`, the
Hospital Coordination Agent (`agents/hospital_agent.py`) attaches a
capacity disclaimer to its recommendation ("reported capacity, not
confirmed live availability") rather than silently treating the bed count
as current truth. This is a deliberate implementation of the "don't let
the AI hallucinate certainty" principle from your research notes — see
`recommend_hospitals()`'s `capacity_caveat` field.

## Path to real data (not done here — this is the roadmap, not a claim)

If you want to replace the dummy CSVs with real data before the hackathon:

1. Manually download the actual CSV/PDF exports from:
   - Sindh Health Dept district-wise facilities: https://health.sindh.gov.pk/district-wise-health-facilities
   - Punjab Health & Population Dept facilities: https://pshealthpunjab.gov.pk/Home/HealthFacilities
   - Sindh Healthcare Commission registered facilities: https://shcc.org.pk/
   - Rescue 1122 Punjab statistics: https://www.rescue.gov.pk/
   - Open Data Pakistan health sites dataset: https://opendata.com.pk/dataset?category=Health&tags=Hospitals
2. Normalize them to match the column headers already used in
   `backend/data/hospitals_sindh_demo.csv` / `hospitals_punjab_demo.csv`
   (add/rename columns as needed — the loader in `seed.py` is a thin CSV
   reader, easy to adjust).
3. Set `trust_level=OFFICIAL` and fill in the real `source_name`/
   `source_url`/`last_verified` for each row you've verified yourself.
4. Re-run `python seed.py --full-reset`.

Doing this properly (cleaning, deduplicating, verifying) is real work and
was explicitly flagged in your own research as the next step, not something
to rush — the dummy dataset here exists so the *pipeline and UI* are fully
demoable now, while that data-acquisition work happens on its own timeline.

## What's NOT included, and why

- No `hospital_capacity`, `data_sources`, `data_updates`, or
  `verification_records` tables (the full 4-layer model from your notes).
  For hackathon scope, the trust fields were added directly onto
  `hospitals` and `resources` instead — simpler, and enough to demo the
  concept convincingly. Splitting into full provenance tables is a good
  "future work" slide, not something worth spending remaining hackathon
  time on.
- No live hospital-status portal (Rescue 1122-style dashboard where
  hospitals log in and update beds). Also flagged as future work in your
  notes — out of scope for this pass.
