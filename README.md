# TrustSphere

TrustSphere is an offline-capable AI security platform designed to demonstrate a modern Security Operations Center workflow across behavioral analytics, attack correlation, and analyst-facing response tooling.

The repository combines three major layers:
- `frontend`: a Stitch-based React SOC console for analysts and administrators
- `security_ai`: the FastAPI serving layer and operational backend APIs
- `trustsphere-ai`: the intelligence engine for UEBA, risk scoring, attack graph generation, and local SOC reasoning

The platform is structured for hackathon demo reliability while preserving a clean path toward a more production-oriented deployment model.

## Platform Scope

TrustSphere supports the following security workflow:
- log ingestion and simulation
- UEBA feature engineering and anomaly detection
- business risk scoring
- attack graph reconstruction and MITRE-aligned correlation
- local SOC analyst reasoning and reporting
- phishing, URL, credential, attachment, and prompt-injection detection
- role-aware SOC operations UI for triage, investigation, response, and reporting

## Architecture

```text
Frontend (React / Next.js)
  ->
FastAPI Backend (`security_ai/api`)
  ->
TrustSphere Intelligence Engine (`trustsphere-ai`)
  ->
UEBA + Risk + Attack Graph + Local SOC Reasoning
```

### Runtime Behavior
- The frontend uses a Stitch-derived enterprise SOC theme.
- The backend exposes a unified API envelope and demo-safe fallbacks.
- The intelligence layer remains the single source of truth for incident analysis.
- Hybrid bootstrap-to-live behavior is supported so the application can load seeded SOC state immediately and transition into live backend updates.

## Key Capabilities

### Intelligence Engine
- behavioral feature engineering
- anomaly detection and inference pipelines
- UEBA risk engine
- attack graph construction and scoring
- local SOC analyst orchestration
- schema registry and pipeline contracts

### Security Models
- phishing email detection
- URL phishing detection
- credential exposure detection
- malicious attachment analysis
- prompt injection defense

### SOC Console
- overview and monitoring
- incidents and investigations
- threat graph analysis
- playbooks and reports
- admin and analyst role separation
- demo-safe polling and hybrid bootstrap/live updates

## Repository Structure

```text
TrustSphere/
  frontend/          # React / Next.js SOC console
  security_ai/       # FastAPI backend, API layer, deployment scaffolding
  trustsphere-ai/    # UEBA, risk, graph, reasoning, contracts, pipelines
  deploy/            # Prometheus and deployment assets
  docker-compose.yml # local multi-service composition
```

## Getting Started

### 1. Start the backend
From the repository root:

```bash
PYTHONPATH=. trustsphere-ai/.venv/bin/python -m uvicorn security_ai.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the frontend
In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:
- [http://localhost:3000](http://localhost:3000)

## Frontend Configuration

The frontend supports the following environment variables:
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_TRUSTSPHERE_API_KEY`
- `NEXT_PUBLIC_API_TIMEOUT_MS`
- `NEXT_PUBLIC_DEMO_MODE`

Example:

```bash
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
export NEXT_PUBLIC_TRUSTSPHERE_API_KEY=trustsphere-local-dev-key
export NEXT_PUBLIC_DEMO_MODE=true
```

## Backend API Style

The backend uses a unified response envelope:

```json
{
  "success": true,
  "data": {},
  "meta": {},
  "error": null
}
```

Representative API groups include:
- `/api/overview/*`
- `/api/events/*`
- `/api/incidents/*`
- `/api/investigations/*`
- `/api/attack-graph/*`
- `/api/playbooks/*`
- `/api/reports/*`
- `/api/admin/*`
- `/detect/*`
- `/guard/prompt`
- `/analyze/incident`

## Demo Readiness

TrustSphere is optimized for reliable demonstrations in constrained environments.

Current demo behavior includes:
- seeded SOC bootstrap state on startup
- automatic transition to live backend mode
- backend-safe fallback responses
- frontend-safe refresh behavior during polling
- role-based analyst and admin views

This keeps the application usable even when parts of the ML or local inference stack are temporarily unavailable.

## Deployment Notes

The repository includes:
- `Dockerfile.security-api`
- `Dockerfile.security-worker`
- `docker-compose.yml`
- Prometheus configuration under `deploy/`

These assets provide a baseline for local service composition and observability-oriented demos.

## Current Positioning

TrustSphere should be understood as:
- a strong integrated hackathon demo platform
- an offline-first SOC intelligence prototype
- a modular foundation for future hardening and operationalization

It should not yet be treated as a finished enterprise production deployment without additional work in testing, security hardening, infrastructure validation, and model operations.
