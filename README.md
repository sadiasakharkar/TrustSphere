# TrustSphere

TrustSphere is a full frontend prototype for a **Cyber Incident Response Dashboard** built for banking/enterprise SOC workflows.

This repo includes:
- `frontend/`: Next.js + React + Tailwind CSS application with production-ready UI prototype
- `backend/`: placeholder structure for future API implementation (no live backend yet)

## Tech Stack
- Next.js 14 (Pages Router)
- React 18
- Tailwind CSS 3
- Chart.js + react-chartjs-2

## Features Implemented
- Dark enterprise theme (`#0D1117`, `#161B22`, cyan/electric-blue accents)
- Login screen with role selector and placeholder auth action
- Dashboard with KPI cards and interactive charts
- Incidents page with filters, risk-scored table, details modal, playbook modal
- Playbooks page with incident summary, attack graph placeholder, response timeline
- Analytics page with trend chart and anomalous entities table
- Settings page with user management and alert source configuration
- Fully responsive layout with collapsible sidebar and top navigation
- Placeholder async backend contracts for future integration

## Repository Structure

```text
TrustSphere/
  frontend/
    assets/
    components/
    data/
    pages/
    services/
    styles/
  backend/
    routes/
    controllers/
    models/
    utils/
```

## Local Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Production Build

```bash
cd frontend
npm run build
npm start
```

## Vercel Deployment
- Import this repository into Vercel.
- Set project root directory to `frontend`.
- Framework preset: Next.js.
- Build command: `npm run build`.
- Output: default Next.js output.

## Backend Placeholder Notes
`frontend/services/apiPlaceholders.js` contains empty async function signatures such as:
- `fetchAlerts()`
- `fetchIncidents(filters)`
- `getPlaybook(incidentId)`
- `fetchAnalytics(range)`
- `fetchUsers()`
- `updateUser(userId, payload)`
- `fetchSettings()`

These are imported across UI pages but intentionally make no real API calls.
