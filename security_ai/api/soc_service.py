"""SOC domain service layer for TrustSphere FastAPI backend."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any


class SOCService:
    """In-memory SOC backend state with deterministic seed data for demo readiness."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._incidents = self._build_incidents()
        self._events = self._build_events()
        self._playbooks = self._build_playbooks()
        self._reports = self._build_reports()
        self._users = self._build_users()
        self._system_status = self._build_system_status()
        self._attack_graph = self._build_attack_graph()

    def get_overview_summary(self) -> dict[str, Any]:
        incidents = list(self._incidents.values())
        critical = sum(1 for item in incidents if item["severity"] == "Critical")
        active = sum(1 for item in incidents if item["status"] != "Resolved")
        open_count = sum(1 for item in incidents if item["status"] == "Open")
        return {
            "headline": {
                "title": "Enterprise SOC Overview",
                "subtitle": "Unified intelligence across UEBA, graph analytics, fraud detectors, and local SOC reasoning.",
                "status": "Air-gapped production simulation",
                "updatedAt": self._now_iso(),
            },
            "metrics": [
                {"label": "Total Alerts", "value": len(self._events), "delta": "+6", "status": "critical", "helper": "24h event window"},
                {"label": "Active Incidents", "value": active, "delta": f"+{max(active - 3, 1)}", "status": "high", "helper": "Open and investigating"},
                {"label": "Critical Alerts", "value": critical, "delta": "+2", "status": "critical", "helper": "Immediate analyst attention"},
                {"label": "Open Incidents", "value": open_count, "delta": "Stable", "status": "healthy", "helper": "Queue currently manageable"},
            ],
            "criticalQueue": sorted(incidents, key=lambda item: item["riskScore"], reverse=True)[:4],
            "modelHealth": [
                {"name": "UEBA Anomaly Model", "status": "Healthy", "detail": "Isolation Forest inference stable. Drift estimate 0.07."},
                {"name": "Attack Graph Engine", "status": "High Activity", "detail": "Critical chains reconstructed from entity pivots in the last 30 minutes."},
                {"name": "SOC LLM Analyst", "status": "Ready", "detail": "Local reasoning pipeline is available with deterministic mode enabled."},
                {"name": "Fraud Detector Suite", "status": "Healthy", "detail": "Email, URL, credential, attachment, and prompt guard are available."},
            ],
        }

    def get_soc_metrics(self) -> dict[str, Any]:
        incidents = list(self._incidents.values())
        return {
            "severityDistribution": {
                "Critical": sum(1 for item in incidents if item["severity"] == "Critical"),
                "High": sum(1 for item in incidents if item["severity"] == "High"),
                "Medium": sum(1 for item in incidents if item["severity"] == "Medium"),
                "Low": sum(1 for item in incidents if item["severity"] == "Low"),
            },
            "recentActivity": self._events[:6],
            "riskDistribution": [item["riskScore"] for item in incidents],
        }

    def get_live_events(self) -> list[dict[str, Any]]:
        return deepcopy(self._events)

    def get_detection_feed(self) -> list[dict[str, Any]]:
        return [
            {"id": "DET-001", "source": "UEBA", "status": "Healthy", "precision": 0.97, "drift": "Low", "lastUpdated": self._now_iso()},
            {"id": "DET-002", "source": "Email AI", "status": "Healthy", "precision": 0.96, "drift": "Low", "lastUpdated": self._now_iso()},
            {"id": "DET-003", "source": "URL AI", "status": "Healthy", "precision": 0.98, "drift": "Low", "lastUpdated": self._now_iso()},
            {"id": "DET-004", "source": "Prompt Guard", "status": "High Activity", "precision": 0.99, "drift": "Low", "lastUpdated": self._now_iso()},
        ]

    def list_incidents(self) -> list[dict[str, Any]]:
        return sorted(deepcopy(list(self._incidents.values())), key=lambda item: item["riskScore"], reverse=True)

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        incident = self._incidents.get(incident_id)
        if incident is None:
            return None
        return {
            **deepcopy(incident),
            "timeline": deepcopy(self._build_incident_timeline(incident_id)),
            "summary": {
                "id": incident["id"],
                "title": incident["title"],
                "severity": incident["severity"],
                "confidence": incident["confidence"],
                "status": incident["status"],
                "owner": incident["owner"],
                "users": incident["users"],
                "hosts": incident["hosts"],
                "mitre": incident["mitre"],
            },
            "evidence": deepcopy(self._build_evidence(incident_id)),
            "relatedAlerts": [event for event in self._events if event["incidentId"] == incident_id],
        }

    def update_incident_status(self, incident_id: str, status: str) -> dict[str, Any] | None:
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident is None:
                return None
            incident["status"] = status
            incident["updatedAt"] = self._now_iso()
            return deepcopy(incident)

    def assign_incident(self, incident_id: str, assignee: str) -> dict[str, Any] | None:
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident is None:
                return None
            incident["owner"] = assignee
            incident["updatedAt"] = self._now_iso()
            return deepcopy(incident)

    def get_investigation_entity(self, entity_id: str) -> dict[str, Any]:
        matched_events = [event for event in self._events if entity_id in {event["entity"], event.get("user", ""), event.get("host", "")}] or self._events[:4]
        return {
            "entity": entity_id,
            "timeline": matched_events,
            "aiSummary": f"{entity_id} shows repeated anomalous activity across authentication, privilege, and network telemetry.",
            "relatedAlerts": [event["id"] for event in matched_events],
        }

    def search_events(self, query: str = "", severity: str | None = None) -> list[dict[str, Any]]:
        query_lower = query.lower().strip()
        rows = self._events
        if query_lower:
            rows = [row for row in rows if query_lower in row["entity"].lower() or query_lower in row["eventType"].lower()]
        if severity:
            rows = [row for row in rows if row["severity"].lower() == severity.lower()]
        return deepcopy(rows)

    def get_attack_graph(self, incident_id: str | None = None) -> dict[str, Any]:
        graph = deepcopy(self._attack_graph)
        if incident_id:
            graph["incidentId"] = incident_id
        graph["riskLevels"] = [node["risk"] for node in graph["nodes"]]
        return graph

    def list_playbooks(self) -> list[dict[str, Any]]:
        return deepcopy(self._playbooks)

    def run_playbook(self, incident_id: str, playbook_id: str | None = None) -> dict[str, Any]:
        incident = self._incidents.get(incident_id)
        selected = next((item for item in self._playbooks if item["id"] == playbook_id), self._playbooks[0])
        return {
            "incidentId": incident_id,
            "incidentTitle": incident["title"] if incident else "Unknown incident",
            "playbook": deepcopy(selected),
            "executionStatus": "READY",
            "startedAt": self._now_iso(),
        }

    def list_reports(self) -> list[dict[str, Any]]:
        return deepcopy(self._reports)

    def export_report(self, report_id: str, export_format: str = "markdown") -> dict[str, Any] | None:
        report = next((item for item in self._reports if item["id"] == report_id), None)
        if report is None:
            return None
        return {
            "reportId": report_id,
            "format": export_format,
            "status": "EXPORTED",
            "exportedAt": self._now_iso(),
            "downloadPath": f"outputs/{report_id}.{ 'json' if export_format == 'json' else 'md'}",
        }

    def get_admin_system(self) -> dict[str, Any]:
        return deepcopy(self._system_status)

    def get_admin_users(self) -> list[dict[str, Any]]:
        return deepcopy(self._users)

    def _build_incidents(self) -> dict[str, dict[str, Any]]:
        rows = [
            {
                "id": "INC-21403",
                "timestamp": "2026-03-24 18:11:17",
                "entity": "acct-payroll-09",
                "eventType": "Privilege Escalation",
                "riskScore": 92,
                "status": "Open",
                "severity": "Critical",
                "affected": "3 hosts, 2 users",
                "owner": "Avery Collins",
                "sla": "12m",
                "tactic": "Privilege Escalation",
                "title": "Suspicious privilege escalation with cross-segment lateral movement",
                "confidence": "0.94",
                "users": ["jane.carter", "svc-payroll-admin"],
                "hosts": ["acct-payroll-09", "dc-east-02"],
                "mitre": ["TA0001 Initial Access", "TA0004 Privilege Escalation", "TA0008 Lateral Movement"],
                "updatedAt": self._now_iso(),
            },
            {
                "id": "INC-21404",
                "timestamp": "2026-03-24 18:19:03",
                "entity": "teller-branch-11",
                "eventType": "Anomalous Login",
                "riskScore": 78,
                "status": "Investigating",
                "severity": "High",
                "affected": "1 host, 1 user",
                "owner": "Unassigned",
                "sla": "21m",
                "tactic": "Credential Access",
                "title": "Impossible-travel authentication sequence",
                "confidence": "0.83",
                "users": ["samir.khan"],
                "hosts": ["teller-branch-11"],
                "mitre": ["TA0006 Credential Access", "TA0001 Initial Access"],
                "updatedAt": self._now_iso(),
            },
            {
                "id": "INC-21405",
                "timestamp": "2026-03-24 18:26:48",
                "entity": "loan-underwrite-03",
                "eventType": "Malware Signature",
                "riskScore": 71,
                "status": "Triaged",
                "severity": "High",
                "affected": "2 hosts",
                "owner": "Riley Grant",
                "sla": "34m",
                "tactic": "Execution",
                "title": "Suspicious execution chain on underwriting host",
                "confidence": "0.79",
                "users": ["svc-underwrite"],
                "hosts": ["loan-underwrite-03"],
                "mitre": ["TA0002 Execution"],
                "updatedAt": self._now_iso(),
            },
            {
                "id": "INC-21406",
                "timestamp": "2026-03-24 18:33:09",
                "entity": "atm-cluster-02",
                "eventType": "Data Exfiltration",
                "riskScore": 88,
                "status": "Escalated",
                "severity": "Critical",
                "affected": "4 hosts, 1 service account",
                "owner": "Maya Patel",
                "sla": "8m",
                "tactic": "Exfiltration",
                "title": "Outbound transfer spike from ATM service cluster",
                "confidence": "0.91",
                "users": ["svc-wire-transfer"],
                "hosts": ["atm-cluster-02"],
                "mitre": ["TA0010 Exfiltration"],
                "updatedAt": self._now_iso(),
            },
        ]
        return {row["id"]: row for row in rows}

    def _build_events(self) -> list[dict[str, Any]]:
        base = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        entities = ["svc-wire-transfer", "acct-payroll-09", "jane.carter", "dc-east-02", "atm-cluster-02", "loan-underwrite-03"]
        event_types = ["after_hours_login", "privilege_change", "mass_file_access", "lateral_move", "data_exfiltration", "token_refresh"]
        severities = ["Critical", "High", "Medium", "High", "Critical", "Medium"]
        rows: list[dict[str, Any]] = []
        for index in range(12):
            rows.append(
                {
                    "id": f"EVT-{3100 + index}",
                    "incidentId": ["INC-21403", "INC-21404", "INC-21405", "INC-21406"][index % 4],
                    "timestamp": (base - timedelta(minutes=index * 3)).strftime("%Y-%m-%d %H:%M:%S"),
                    "entity": entities[index % len(entities)],
                    "user": entities[index % len(entities)] if "." in entities[index % len(entities)] else "",
                    "host": entities[index % len(entities)] if "-" in entities[index % len(entities)] else "",
                    "source": ["UEBA", "Email AI", "URL AI", "Prompt Guard"][index % 4],
                    "eventType": event_types[index % len(event_types)],
                    "severity": severities[index % len(severities)],
                    "score": [92, 86, 71, 77, 88, 69][index % 6],
                }
            )
        return rows

    def _build_playbooks(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "PLB-001",
                "name": "Privilege escalation containment",
                "steps": [
                    {"title": "Containment", "detail": "Disable impacted credentials and isolate privileged endpoints.", "owner": "SOC Tier-1", "confidence": 96},
                    {"title": "Investigation", "detail": "Correlate IAM, EDR, and UEBA events against MITRE techniques.", "owner": "Threat Hunt", "confidence": 93},
                    {"title": "Recovery", "detail": "Restore normal access after validating clean authentication paths.", "owner": "Platform Ops", "confidence": 89},
                ],
            }
        ]

    def _build_reports(self) -> list[dict[str, Any]]:
        return [
            {"id": "RPT-201", "title": "Executive summary: payroll lateral movement", "severity": "Critical", "author": "TrustSphere SOC Analyst", "updated": "2026-03-24 18:31"},
            {"id": "RPT-202", "title": "Containment plan: external transfer suppression", "severity": "High", "author": "Avery Collins", "updated": "2026-03-24 17:52"},
        ]

    def _build_users(self) -> list[dict[str, Any]]:
        return [
            {"id": "U-001", "name": "Avery Collins", "role": "Analyst", "status": "Active"},
            {"id": "U-002", "name": "Maya Patel", "role": "Admin", "status": "Active"},
            {"id": "U-003", "name": "Jordan Lee", "role": "Analyst", "status": "Suspended"},
            {"id": "U-004", "name": "Riley Grant", "role": "Analyst", "status": "Active"},
        ]

    def _build_system_status(self) -> dict[str, Any]:
        return {
            "environment": "offline-demo",
            "queue": "Nominal",
            "worker": "Ready",
            "kafka": "Connected",
            "ollama": "Ready",
            "lastUpdated": self._now_iso(),
        }

    def _build_attack_graph(self) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": "n1", "label": "jane.carter", "type": "user", "risk": "critical", "x": 18, "y": 45},
                {"id": "n2", "label": "acct-payroll-09", "type": "host", "risk": "high", "x": 36, "y": 28},
                {"id": "n3", "label": "dc-east-02", "type": "host", "risk": "critical", "x": 56, "y": 48},
                {"id": "n4", "label": "185.193.12.44", "type": "ip", "risk": "critical", "x": 82, "y": 35},
            ],
            "edges": [
                {"from": "n1", "to": "n2", "label": "credential_use"},
                {"from": "n2", "to": "n3", "label": "lateral_move"},
                {"from": "n3", "to": "n4", "label": "exfiltration"},
            ],
            "chains": [
                {"id": "AG-204", "title": "Credential misuse to exfiltration chain", "severity": "Critical", "confidence": "0.92"},
                {"id": "AG-198", "title": "Suspicious admin token pivot", "severity": "High", "confidence": "0.81"},
            ],
        }

    def _build_incident_timeline(self, incident_id: str) -> list[dict[str, Any]]:
        default = [
            {"time": "02:14", "title": "Impossible-travel login detected", "detail": "User jane.carter authenticated from a new geography."},
            {"time": "02:19", "title": "Privileged token requested", "detail": "Service account elevation observed outside baseline."},
            {"time": "02:27", "title": "Lateral movement to domain controller", "detail": "Remote admin execution created on dc-east-02."},
            {"time": "02:41", "title": "High-volume outbound transfer", "detail": "Encrypted exfiltration path established to external IP."},
        ]
        if incident_id == "INC-21404":
            return [
                {"time": "03:04", "title": "Impossible travel detected", "detail": "Authentication originated from a new geography within 20 minutes of local access."},
                {"time": "03:09", "title": "Unknown device fingerprint", "detail": "Login session continued from a new device signature."},
                {"time": "03:14", "title": "Escalated monitoring", "detail": "Branch terminal placed under active investigation."},
            ]
        return default

    def _build_evidence(self, incident_id: str) -> list[dict[str, Any]]:
        return [
            {"title": "Behavioral deviation", "content": f"{incident_id} exceeds expected after-hours activity and device consistency thresholds."},
            {"title": "Credential risk", "content": "Failed login burst followed by success from a new device fingerprint."},
            {"title": "Graph correlation", "content": "Attack chain intersects sensitive infrastructure and privileged assets."},
        ]

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
