# TrustSphere - Offline ACIRS Prototype

TrustSphere is a hackathon-grade frontend prototype for an **AI-driven Autonomous Cyber Incident Response System (ACIRS)** in banking environments.

The UI is fully offline-focused, role-aware, and designed to explain end-to-end incident response flow without backend connectivity.

## Highlights
- Dark enterprise SOC theme (`#0D1117`, `#161B22`, cyan/teal/violet accents)
- Role-based UI rendering:
  - **Analyst**: dashboards, incidents, playbooks, analytics, limited settings
  - **Admin**: all analyst views + user management, system configuration, model training status, audit logs
- Air-gapped offline visual cues and narrative-first incident explainability
- Animated charts, risk/severity badges, modals, and responsive layout
- Backend scaffold included for future integration

## Repository Structure

```text
TrustSphere/
  frontend/
    pages/        # login, dashboard, incidents, playbooks, analytics, settings
    components/   # Sidebar, Navbar, Card, Table, Modal, Chart, Badge, Alert
    context/      # role/session management
    assets/       # static visuals/icons
    styles/       # global styles + Tailwind theme mapping
    services/     # placeholder API signatures
    data/         # realistic mock data
  backend/
    routes/       # alerts.js, incidents.js, users.js (+ placeholders)
    controllers/  # placeholder files
    models/       # placeholder files
    utils/        # placeholder files
```

## Run Locally

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Build

```bash
cd frontend
npm run build
npm start
```

## Vercel Deployment
- Import this repository in Vercel.
- Set **Root Directory** to `frontend`.
- Framework preset: **Next.js**.
- Build command: `npm run build`.

## Backend Integration Ready
`frontend/services/apiPlaceholders.js` provides empty async contracts (e.g., `fetchIncidents`, `getPlaybook`, `fetchAuditLogs`) to preserve stable signatures for future API wiring.
