---
title: RescueAI
emoji: 🚨
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# RescueAI — AI Emergency Response & Resource Coordination System

A decision-support platform that turns fragmented emergency reports into an
explainable, resource-aware, **human-approved** response plan.

> **Safety principle:** RescueAI never autonomously dispatches real emergency
> personnel. Every AI recommendation flows through
> `Emergency Info → AI Analysis → AI Recommendation → Human Review → Human
> Approval → Simulated Dispatch`. All data in this repo is synthetic/demo data.

---

## 1. Architecture

```
rescueai/
├── backend/
│   ├── agents/              # The 6 agents + orchestrator + RAG
│   │   ├── intake_agent.py       # Agent 1: raw text -> structured incident
│   │   ├── analysis_agent.py     # Agent 2: severity/urgency + explanation
│   │   ├── resource_agent.py     # Agent 3: multi-factor resource matching
│   │   ├── hospital_agent.py     # Agent 4: hospital capacity scoring
│   │   ├── risk_agent.py         # Agent 5: secondary-risk identification
│   │   ├── planning_agent.py     # Agent 6: combines everything into a plan
│   │   ├── knowledge_base.py     # Lightweight RAG retriever
│   │   └── orchestrator.py       # Runs the pipeline; conflict detection
│   ├── routers/              # FastAPI route handlers
│   ├── knowledge_base/       # RAG source docs (markdown, by category)
│   ├── tests/                # Unit tests (stdlib unittest, no DB needed)
│   ├── models.py             # SQLAlchemy ORM (9 tables)
│   ├── schemas.py            # Pydantic request/response models
│   ├── database.py           # DB engine/session (SQLite by default)
│   ├── main.py                # FastAPI app
│   └── seed.py                # Synthetic demo data loader
├── frontend/
│   └── src/
│       ├── pages/            # Dashboard, Incidents, Detail, Resources,
│       │                     # Hospitals, Map, Analytics, Notifications, Audit
│       ├── components/       # SeverityBadge, MapView, ResponsePlanPanel, ...
│       └── api/client.js     # Backend API wrapper
├── docker-compose.yml
└── .env.example
```

### Why rule-based/explainable agents instead of raw LLM calls?

Each agent is implemented as transparent, deterministic logic (keyword
extraction, weighted scoring, lookup tables) rather than an opaque model
call. For a **decision-support system whose core requirement is
explainability and human trust**, this means every severity score, resource
pick, and hospital recommendation traces back to a concrete, inspectable
reason — no hidden chain-of-thought to hide or hallucinate. `LLM_API_KEY` /
`MODEL_NAME` are wired into `.env.example` as a deliberate extension point:
swapping `intake_agent.classify()` (or any other agent's core function) for
a real LLM call is a drop-in change that preserves the same structured
input/output contract, and you can layer that in for the parts that would
most benefit (e.g., open-ended entity extraction) without touching the rest
of the pipeline.

---

## 2. Quick start (zero external dependencies)

### Option A — Docker (recommended for judges)

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173

### Option B — Run locally

**Backend:**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python seed.py                 # loads synthetic resources/hospitals/users
uvicorn main:app --reload      # http://localhost:8000
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

The frontend's dev server proxies `/api/*` to `http://localhost:8000` (see
`vite.config.js`), so no CORS configuration is needed in development.

> **Note on this repository's provenance:** every backend Python file has
> been syntax-checked (`py_compile`) and the full 6-agent pipeline has been
> exercised end-to-end with a standalone test harness (see
> `backend/tests/test_agents.py` — 13 tests, all passing) reproducing the
> spec's sample scenario almost exactly. The frontend has been syntax- and
> bundle-checked with esbuild (confirming all imports/exports resolve). It
> was built in a network-isolated environment, so `pip install` / `npm
> install` / a live end-to-end server run have **not** been performed by the
> author — do this first thing after downloading, and please file an issue
> (or just fix it — it's a hackathon MVP!) if anything doesn't come up clean.

---

## 2b. Free deployment: Hugging Face Spaces + Google Colab

Two free options, good for different things:

- **Hugging Face Spaces (Docker)** — the recommended way to get a
  persistent, always-on public URL for free. Good for judges, a portfolio
  link, or a demo you can share.
- **Google Colab** — good for quickly spinning up a temporary public API
  endpoint (e.g. to test the backend from a phone, or share a link with a
  teammate for an hour) using a tunnel. **Not** suited for a persistent
  deployment: the notebook's runtime disconnects after inactivity/~12h, the
  tunnel URL changes every time you rerun it, and Colab isn't meant to serve
  production traffic.

### Deploy the full app to Hugging Face Spaces (free CPU tier)

The root `Dockerfile` builds the frontend and bundles it together with the
backend into a single image that serves everything on one port — this is
exactly what a Space needs (Spaces host one container per app).

1. Go to https://huggingface.co/new-space
2. Pick a name, set **SDK = Docker**, visibility as you like, and choose the
   free **CPU basic** hardware tier.
3. Push this repo's contents to the Space (Spaces are just git repos):
   ```bash
   git clone https://huggingface.co/spaces/<your-username>/<your-space-name>
   cp -r rescueai/* rescueai/.dockerignore <your-space-name>/
   cd <your-space-name>
   git add .
   git commit -m "Deploy RescueAI"
   git push
   ```
4. The root `README.md` already has the YAML frontmatter Spaces need
   (`sdk: docker`, `app_port: 7860`) — don't remove it.
5. The Space will build the root `Dockerfile`, which runs `seed.py` then
   `uvicorn` on port 7860, serving the React frontend at `/` and the API
   under `/api/*` (Swagger docs at `/docs`).

**Important limitation to know about:** the free tier's filesystem is
ephemeral — every time the Space restarts (e.g. after being idle, or on a
redeploy), the SQLite database resets and reseeds from scratch. That's
actually fine for a demo (every visitor gets a clean slate), but if you want
data to persist, either enable a Space's *persistent storage* add-on (paid)
or point `DATABASE_URL` at an external free Postgres (e.g. a free-tier
Neon.tech or Supabase instance) via the Space's **Settings → Repository
secrets**.

### Quick, temporary public API via Google Colab

Use this when you just want a live, shareable URL for the *backend API*
right now, without deploying anywhere. A ready-made notebook is at
`deploy/colab_run_backend.ipynb` — or create a new Colab notebook and run:

```python
# Cell 1 - get the code onto the Colab VM
# (upload the project as a zip via the Colab file browser, or clone your repo)
!unzip -q rescueai.zip -d /content/app
%cd /content/app/rescueai/backend

# Cell 2 - install dependencies
!pip install -q fastapi uvicorn sqlalchemy pydantic python-dotenv pyngrok

# Cell 3 - seed demo data
!python seed.py

# Cell 4 - run the API and expose it publicly via ngrok
from pyngrok import ngrok
import subprocess, time

# Sign up free at https://dashboard.ngrok.com and paste your authtoken below
ngrok.set_auth_token("YOUR_NGROK_AUTHTOKEN")

proc = subprocess.Popen(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])
time.sleep(3)
public_url = ngrok.connect(8000)
print("Public API URL:", public_url)
print("Swagger docs:  ", f"{public_url}/docs")
```

This gives you a public `https://....ngrok-free.app` URL you can hit from
anywhere (Postman, a browser, or a separately-hosted frontend) for as long
as the Colab runtime and ngrok tunnel stay alive. For anything longer-lived,
use the Hugging Face Space above instead.

---

## 3. Database

PostgreSQL-compatible via `DATABASE_URL`; defaults to a local SQLite file
(`rescueai.db`) so the whole thing runs with zero setup. Tables: `users`,
`incidents`, `incident_reports`, `resources`, `resource_assignments`,
`hospitals`, `response_plans`, `notifications`, `audit_logs` — see
`backend/models.py` for full schema.

To use real PostgreSQL: uncomment the `db` service in `docker-compose.yml`
and set `DATABASE_URL=postgresql+psycopg2://rescueai:rescueai@db:5432/rescueai`.

---

## 3b. Dataset (dummy, clearly labeled — see `backend/data/SOURCES.md`)

`seed.py` no longer hard-codes Karachi coordinates in Python — it loads from
CSV files in `backend/data/`:

| File | Contents |
|---|---|
| `hospitals_sindh_demo.csv` | 5 synthetic Sindh-region hospitals, structured like the real Sindh Health Dept district facility directory |
| `hospitals_punjab_demo.csv` | 5 synthetic Punjab-region hospitals, structured like the real Punjab Health Dept directory |
| `resources_demo.csv` | 16 synthetic ambulances/rescue teams/fire units/etc. across Karachi + Lahore |
| `rescue1122_stats_demo.csv` | 7 synthetic rows of historical emergency-call statistics, shaped like Rescue 1122's published reports (not yet wired into the agents — reference data for future analytics) |

**Every row is explicitly synthetic** — names end in `(DEMO)`, and every
record carries `trust_level=DEMO` plus a `source_name` saying so. Nothing
here was scraped from a live government source (this was built with no
network access, and fabricating real-looking numbers would be dishonest).
`backend/data/SOURCES.md` explains exactly why, what a `trust_level` field
means for the AI's behavior (see the hospital capacity caveat below), and
the concrete steps to swap in real data later.

**New provenance fields** on `hospitals` and `resources`: `source_name`,
`source_url`, `trust_level` (`OFFICIAL`/`LIVE`/`REPORTED`/`PUBLIC`/`DEMO`),
`last_verified`. The Hospital Coordination Agent uses this: unless a
hospital's `trust_level` is `LIVE`, its recommendation includes an explicit
caveat that bed/ICU counts are *reported*, not *confirmed available right
now* — visible in the Response Plan panel and on the Hospitals page.

---

## 4. API reference (all endpoints, see also `/docs` for interactive Swagger UI)

| Method | Path | Purpose |
|---|---|---|
| POST | `/incidents` | Submit a raw emergency report → Agent 1 structures it |
| POST | `/incidents/{id}/reports` | Add another report (demonstrates conflict detection) |
| GET | `/incidents` | List incidents (filter by `status`, `severity`) |
| GET | `/incidents/{id}` | Incident detail incl. all reports |
| POST | `/incidents/{id}/analyze` | Run Agents 2–6, generate response plan |
| GET | `/incidents/{id}/response-plan` | Fetch the latest AI response plan |
| POST | `/incidents/{id}/approve` | **Human approval** → triggers simulated dispatch |
| POST | `/incidents/{id}/reject` | Reject the AI plan |
| POST | `/incidents/{id}/resolve` | Mark incident resolved |
| GET | `/resources`, `/resources/available` | Resource inventory |
| GET | `/hospitals` | Hospital inventory |
| GET | `/dashboard/stats` | Command-center summary stats |
| GET | `/dashboard/analytics` | Charts data (by type/severity/utilization) |
| GET | `/audit-logs` | Full audit trail |
| GET | `/notifications` | Simulated dispatch notifications |
| POST | `/demo/load-scenario` | **Demo mode**: loads the spec's building-collapse scenario in one click |

---

## 5. Demo Mode walkthrough (for judges)

1. Open the frontend → **Dashboard**.
2. Click **"▶ Load Demo Incident"** — this loads the exact sample scenario
   from the spec (building collapse, Market Road, ~15 trapped, smoke) *plus*
   two deliberately conflicting follow-up reports (5 vs 20 people).
3. You'll land on the Incident Detail page. Note the
   **CONFLICTING INFORMATION DETECTED** banner and the reliability tags on
   each report (Field Officer = HIGH, Social Media = LOW).
4. Click **"Run AI Analysis"** — this fires Agents 2 through 6 in sequence.
5. Review the AI Response Recommendation: severity, resources (with
   distance/workload reasoning, not just "nearest"), recommended hospital,
   secondary risks, response sequence, confidence scores per field, and an
   expandable "Why this recommendation?" explainability panel citing the
   RAG knowledge base.
6. Click **APPROVE RESPONSE** (as e.g. "Commander Amir Khan") — resource
   statuses flip to `DISPATCHED`, assignment records are created, and a
   simulated notification appears under **Notifications**.
7. Check **Audit Logs** to see the full trail: report added → AI analysis →
   plan generated → approved → simulated dispatch.
8. Browse **Map**, **Resources**, **Hospitals**, and **Analytics** to see
   the rest of the command-center dashboard.

You can also submit your own free-text report from the **Incidents** page
to see Agent 1 classify a different incident type (try mentioning "flood",
"road accident", "fire", etc.).

---

## 6. Test cases

```bash
cd backend
python -m unittest tests.test_agents -v
```

13 tests covering: incident-type classification, severity scoring,
conflicting-report detection, "don't just pick the nearest resource"
behavior, hospital trauma-capacity weighting, gap reporting when no
resource/hospital is available, RAG retrieval, and a full end-to-end replay
of the spec's sample scenario.

---

## 7. Roles & security model

Roles (`ADMIN`, `COMMANDER`, `DISPATCHER`, `FIELD_RESPONDER`,
`HOSPITAL_COORDINATOR`, `VIEWER`) are modeled in the `users` table. For
hackathon scope, the API does not yet enforce per-endpoint role checks (no
auth middleware) — the `approved_by` field on `/approve` records *who*
approved for audit purposes, but does not itself authenticate them. Adding
a real auth layer (e.g. JWT + a dependency that checks role before allowing
`/approve`) is the natural next step and is called out here explicitly
rather than silently assumed to already work.

---

## 8. What's simulated vs. real

| Feature | Status |
|---|---|
| Resource dispatch | **Simulated** — status changes in DB only, no real-world call/API |
| Hospital notification | **Simulated** — a `Notification` row, not a real message |
| Map locations | **Synthetic** coordinates around Karachi, not real units |
| RAG knowledge base | Real retrieval logic, but **synthetic/authored** guidance docs, not an official emergency-management corpus |
| AI agents | Real, deterministic, explainable logic — not calling an external LLM by default (see `LLM_API_KEY` extension point above) |

---

## 9. Presentation flow (suggested, ~5 min)

1. **Problem** (30s): During a crisis, information is fragmented and
   contradictory, and responders are overwhelmed — fast, defensible triage
   decisions are hard under uncertainty.
2. **Live demo** (3 min): Load Demo Incident → show conflict detection →
   Run AI Analysis → walk through the explainability panel → Approve →
   show simulated dispatch + audit log.
3. **Architecture** (1 min): 6-agent pipeline diagram (below), emphasize
   human-in-the-loop gate.
4. **Why this matters** (30s): The AI never replaces the responder — it
   compresses the time between "fragmented reports" and "an informed,
   accountable decision."

### Architecture diagram (text form)

```
[Raw Reports] --> [Agent 1: Intake] --> [Structured Incident]
                                              |
                       +----------------------+----------------------+
                       v                      v                      v
              [Agent 2: Analysis]     [Agent 5: Risk]        [Conflict Detection]
                       |                      |                      |
                       +----------+-----------+----------------------+
                                  v
                       [Agent 3: Resources] --- [Agent 4: Hospitals]
                                  |                      |
                                  +----------+-----------+
                                             v
                                [Agent 6: Response Planning]
                                             v
                              [AI Recommendation + Explainability]
                                             v
                              === HUMAN APPROVAL GATE ===
                                             v
                              [Simulated Dispatch + Audit Log]
```
