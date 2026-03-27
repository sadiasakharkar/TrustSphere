"""SOC domain service layer for TrustSphere FastAPI backend."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import random
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
        self._random = random.Random(42)
        self._bootstrap_mode = True
        self._stream_counter = 0
        self._bootstrap_duration_seconds = 7
        self._bootstrap_started_at = self._now_iso()
        self._bootstrap_state = self.generate_bootstrap_state()

    async def activate_bootstrap_transition(self, duration_seconds: int | None = None) -> None:
        self._bootstrap_mode = True
        self._bootstrap_started_at = self._now_iso()
        self._bootstrap_duration_seconds = duration_seconds or self._bootstrap_duration_seconds
        self._bootstrap_state = self.generate_bootstrap_state()
        await asyncio.sleep(self._bootstrap_duration_seconds)
        with self._lock:
            self._bootstrap_mode = False
            self._system_status["environment"] = "live-ai-mode"
            self._system_status["lastUpdated"] = self._now_iso()

    async def run_streaming_updates(self) -> None:
        while True:
            await asyncio.sleep(2 if self._bootstrap_mode else 5)
            with self._lock:
                self._stream_counter += 1
                if self._bootstrap_mode:
                    self._tick_bootstrap_state()
                else:
                    self._tick_live_state()

    def response_meta(self) -> dict[str, Any]:
        return {
            "mode": "bootstrap" if self._bootstrap_mode else "live",
            "bootstrapMode": self._bootstrap_mode,
            "streamCounter": self._stream_counter,
            "startedAt": self._bootstrap_started_at,
        }

    def get_overview_summary(self) -> dict[str, Any]:
        if self._bootstrap_mode:
            return deepcopy(self._bootstrap_state["overview"])
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
            "demoScenario": {
                "title": "Credential compromise leading to privileged lateral movement",
                "focusIncidentId": "INC-21403",
                "summary": "A payroll identity pivot coincides with domain-controller movement and outbound transfer preparation.",
            },
            "modelHealth": [
                {"name": "UEBA Anomaly Model", "status": "Healthy", "detail": "Isolation Forest inference stable. Drift estimate 0.07."},
                {"name": "Attack Graph Engine", "status": "High Activity", "detail": "Critical chains reconstructed from entity pivots in the last 30 minutes."},
                {"name": "SOC LLM Analyst", "status": "Ready", "detail": "Local reasoning pipeline is available with deterministic mode enabled."},
                {"name": "Fraud Detector Suite", "status": "Healthy", "detail": "Email, URL, credential, attachment, and prompt guard are available."},
            ],
        }

    def get_soc_metrics(self) -> dict[str, Any]:
        if self._bootstrap_mode:
            return deepcopy(self._bootstrap_state["metrics"])
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
            "spikeSummary": {
                "label": "Active anomaly spike",
                "window": "Last 30 minutes",
                "detail": "Privilege escalation, impossible-travel authentication, and exfiltration signals are clustered around two active incidents.",
            },
        }

    def get_live_events(self) -> list[dict[str, Any]]:
        if self._bootstrap_mode:
            return deepcopy(self._bootstrap_state["events"])
        return deepcopy(self._events)

    def get_detection_feed(self) -> list[dict[str, Any]]:
        if self._bootstrap_mode:
            return deepcopy(self._bootstrap_state["detections"])
        return [
            {"id": "DET-001", "source": "UEBA", "status": "High Activity", "precision": 0.97, "drift": "Low", "lastUpdated": self._now_iso()},
            {"id": "DET-002", "source": "Email AI", "status": "Healthy", "precision": 0.96, "drift": "Low", "lastUpdated": self._now_iso()},
            {"id": "DET-003", "source": "URL AI", "status": "Healthy", "precision": 0.98, "drift": "Low", "lastUpdated": self._now_iso()},
            {"id": "DET-004", "source": "Prompt Guard", "status": "High Activity", "precision": 0.99, "drift": "Low", "lastUpdated": self._now_iso()},
        ]

    def list_incidents(self) -> list[dict[str, Any]]:
        if self._bootstrap_mode:
            return sorted(deepcopy(list(self._bootstrap_state["incidents"].values())), key=lambda item: item["riskScore"], reverse=True)
        return sorted(deepcopy(list(self._incidents.values())), key=lambda item: item["riskScore"], reverse=True)

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        if self._bootstrap_mode:
            incident = self._bootstrap_state["incidents"].get(incident_id)
            if incident is None:
                return None
            return deepcopy(incident)
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
        if self._bootstrap_mode:
            matched_events = [event for event in self._bootstrap_state["events"] if entity_id in {event["entity"], event.get("user", ""), event.get("host", "")}] or self._bootstrap_state["events"][:4]
            return {
                "entity": entity_id,
                "timeline": matched_events,
                "aiSummary": f"{entity_id} is participating in a seeded bootstrap incident chain with abnormal access and pivot behavior.",
                "relatedAlerts": [event["id"] for event in matched_events],
            }
        matched_events = [event for event in self._events if entity_id in {event["entity"], event.get("user", ""), event.get("host", "")}] or self._events[:4]
        return {
            "entity": entity_id,
            "timeline": matched_events,
            "aiSummary": f"{entity_id} shows repeated anomalous activity across authentication, privilege, and network telemetry.",
            "relatedAlerts": [event["id"] for event in matched_events],
        }

    def search_events(self, query: str = "", severity: str | None = None) -> list[dict[str, Any]]:
        query_lower = query.lower().strip()
        rows = self._bootstrap_state["events"] if self._bootstrap_mode else self._events
        if query_lower:
            rows = [row for row in rows if query_lower in row["entity"].lower() or query_lower in row["eventType"].lower()]
        if severity:
            rows = [row for row in rows if row["severity"].lower() == severity.lower()]
        return deepcopy(rows)

    def get_attack_graph(self, incident_id: str | None = None) -> dict[str, Any]:
        graph = deepcopy(self._bootstrap_state["attackGraph"] if self._bootstrap_mode else self._attack_graph)
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
        system = deepcopy(self._system_status)
        system["mode"] = "bootstrap" if self._bootstrap_mode else "live"
        system["streamCounter"] = self._stream_counter
        system["lastUpdated"] = self._now_iso()
        system["modelHealth"] = self._bootstrap_state["modelHealth"] if self._bootstrap_mode else self.get_detection_feed()
        return system

    def get_admin_users(self) -> list[dict[str, Any]]:
        return deepcopy(self._users)

    def generate_bootstrap_state(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        scenarios = [
            ("BOOT-9101", "Impossible travel login against payroll admin", "Critical", "Open", "Avery Collins", "TA0001 Initial Access", 0.97, 96, ["jane.carter", "acct-payroll-09", "185.193.12.44"]),
            ("BOOT-9102", "Brute-force login attempts against branch terminal", "High", "Investigating", "Riley Grant", "TA0006 Credential Access", 0.88, 84, ["samir.khan", "teller-branch-11", "102.88.14.19"]),
            ("BOOT-9103", "Privilege escalation attempt on domain controller", "Critical", "Escalated", "Maya Patel", "TA0004 Privilege Escalation", 0.95, 93, ["svc-payroll-admin", "dc-east-02", "10.11.4.20"]),
            ("BOOT-9104", "Suspicious outbound transfer from ATM cluster", "Critical", "Open", "Avery Collins", "TA0010 Exfiltration", 0.93, 91, ["svc-wire-transfer", "atm-cluster-02", "185.193.12.44"]),
            ("BOOT-9105", "Phishing lure triggered privileged attachment open", "High", "Triaged", "Jordan Lee", "TA0001 Initial Access", 0.82, 79, ["maya.patel", "mail-gateway-01", "44.213.20.77"]),
            ("BOOT-9106", "Lateral movement chain from payroll host", "Critical", "Investigating", "Avery Collins", "TA0008 Lateral Movement", 0.9, 89, ["svc-payroll-admin", "acct-payroll-09", "dc-east-02"]),
            ("BOOT-9107", "Suspicious URL access to credential harvesting site", "Medium", "Open", "Unassigned", "TA0001 Initial Access", 0.73, 67, ["branch.user-22", "branch-kiosk-03", "198.51.100.88"]),
            ("BOOT-9108", "Credential exposure detected in internal paste", "High", "Investigating", "Riley Grant", "TA0006 Credential Access", 0.79, 76, ["svc-underwrite", "git-internal-01", "10.12.0.17"]),
            ("BOOT-9109", "Prompt injection attempt against local analyst", "Medium", "Open", "Unassigned", "TA0005 Defense Evasion", 0.68, 61, ["analyst.console", "soc-console-01", "127.0.0.1"]),
            ("BOOT-9110", "Anomalous admin action after MFA fatigue burst", "High", "Open", "Maya Patel", "TA0006 Credential Access", 0.86, 81, ["admin.ops", "iam-gateway-02", "203.0.113.41"]),
        ]

        incidents: dict[str, dict[str, Any]] = {}
        events: list[dict[str, Any]] = []
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        model_health = [
            {"name": "UEBA Anomaly Model", "status": "Bootstrapping", "detail": "Behavioral inference warming with seeded incident state."},
            {"name": "Attack Graph Engine", "status": "Bootstrapping", "detail": "Graph relationships primed from synthetic SOC movement."},
            {"name": "SOC LLM Analyst", "status": "Ready", "detail": "Local reasoning ready while live mode activates."},
            {"name": "Fraud Detector Suite", "status": "Healthy", "detail": "Email, URL, credential, attachment, and prompt guard seeded."},
        ]

        for index, (incident_id, title, severity, status, assignee, mitre_stage, anomaly_score, risk_score, entities) in enumerate(scenarios):
            created_at = (now - timedelta(minutes=4 * index)).strftime("%Y-%m-%d %H:%M:%S")
            user, host, ip = entities
            timeline = [
                {"time": (now - timedelta(minutes=4 * index + 6)).strftime("%H:%M"), "title": "Initial signal detected", "detail": f"{title} entered the SOC telemetry window."},
                {"time": (now - timedelta(minutes=4 * index + 3)).strftime("%H:%M"), "title": "Entity correlation confirmed", "detail": f"{user} and {host} correlated through {mitre_stage}."},
                {"time": (now - timedelta(minutes=4 * index)).strftime("%H:%M"), "title": "Incident promoted to triage", "detail": f"Risk score elevated to {risk_score} with analyst visibility."},
            ]
            graph_nodes = [
                {"id": f"{incident_id}-u", "label": user, "type": "user", "risk": severity.lower(), "x": 18 + (index % 3) * 8, "y": 24 + (index % 4) * 12},
                {"id": f"{incident_id}-h", "label": host, "type": "host", "risk": "high" if severity != "Medium" else "medium", "x": 46 + (index % 2) * 9, "y": 36 + (index % 3) * 10},
                {"id": f"{incident_id}-i", "label": ip, "type": "ip", "risk": severity.lower(), "x": 76 - (index % 3) * 7, "y": 26 + (index % 5) * 9},
            ]
            graph_edges = [
                {"from": f"{incident_id}-u", "to": f"{incident_id}-h", "label": "login_from"},
                {"from": f"{incident_id}-h", "to": f"{incident_id}-i", "label": "connected_to"},
            ]
            incident = {
                "id": incident_id,
                "timestamp": created_at,
                "entity": host,
                "eventType": title,
                "riskScore": risk_score,
                "status": status,
                "severity": severity,
                "affected": f"{1 + index % 4} hosts, {1 + index % 2} users",
                "owner": assignee,
                "assigned_to": assignee,
                "sla": f"{8 + index * 3}m",
                "tactic": mitre_stage,
                "title": title,
                "confidence": f"{anomaly_score:.2f}",
                "anomaly_score": anomaly_score,
                "users": [user],
                "hosts": [host],
                "mitre": [mitre_stage],
                "mitre_stage": mitre_stage,
                "created_at": created_at,
                "updatedAt": self._now_iso(),
                "entities": entities,
                "timeline": timeline,
                "graph_nodes": graph_nodes,
                "graph_edges": graph_edges,
                "summary": {
                    "id": incident_id,
                    "title": title,
                    "severity": severity,
                    "confidence": f"{anomaly_score:.2f}",
                    "status": status,
                    "owner": assignee,
                    "users": [user],
                    "hosts": [host],
                    "mitre": [mitre_stage],
                },
                "evidence": [
                    {"title": "Behavioral anomaly", "content": f"{user} deviated from baseline with anomaly score {anomaly_score:.2f}."},
                    {"title": "Risk posture", "content": f"Composite risk score is {risk_score} with {mitre_stage} mapping."},
                    {"title": "Operational note", "content": f"{host} and {ip} remain active in the correlated chain."},
                ],
                "relatedAlerts": [],
            }
            incidents[incident_id] = incident
            nodes.extend(graph_nodes)
            edges.extend(graph_edges)

        event_templates = [
            "impossible_travel_login",
            "login_failed_burst",
            "privilege_change",
            "data_exfiltration",
            "phishing_detection",
            "lateral_move",
            "suspicious_url_access",
            "credential_exposure",
            "prompt_injection_attempt",
            "unknown_device",
        ]
        severities = ["Critical", "High", "High", "Critical", "High", "Critical", "Medium", "High", "Medium", "Medium"]
        sources = ["UEBA", "UEBA", "UEBA", "UEBA", "Email AI", "Attack Graph", "URL AI", "Credential AI", "Prompt Guard", "UEBA"]

        incident_rows = list(incidents.values())
        for idx in range(50):
            incident = incident_rows[idx % len(incident_rows)]
            event_type = event_templates[idx % len(event_templates)]
            event = {
                "id": f"BOOT-EVT-{4000 + idx}",
                "incidentId": incident["id"],
                "timestamp": (now - timedelta(minutes=idx)).strftime("%Y-%m-%d %H:%M:%S"),
                "entity": incident["entity"],
                "user": incident["users"][0],
                "host": incident["hosts"][0],
                "source": sources[idx % len(sources)],
                "eventType": event_type,
                "severity": severities[idx % len(severities)],
                "score": min(99, incident["riskScore"] - (idx % 7)),
            }
            events.append(event)
            incident["relatedAlerts"].append(event)

        attack_graph = {
            "nodes": nodes[:18],
            "edges": edges[:18],
            "chains": [
                {"id": "BOOT-CHAIN-01", "title": "Credential misuse to privileged pivot", "severity": "Critical", "confidence": "0.95"},
                {"id": "BOOT-CHAIN-02", "title": "Phishing to suspicious URL sequence", "severity": "High", "confidence": "0.84"},
            ],
            "riskLevels": [node["risk"] for node in nodes[:18]],
        }

        overview = {
            "headline": {
                "title": "Enterprise SOC Overview",
                "subtitle": "Bootstrap intelligence is active while live AI mode initializes.",
                "status": "Live mode activating",
                "updatedAt": self._now_iso(),
            },
            "metrics": [
                {"label": "Active Incidents", "value": len(incidents), "delta": "+4", "status": "critical", "helper": "Bootstrap incident queue"},
                {"label": "Critical Incidents", "value": sum(1 for incident in incidents.values() if incident["severity"] == "Critical"), "delta": "+1", "status": "critical", "helper": "Immediate analyst attention"},
                {"label": "MTTD", "value": "06m", "delta": "-1m", "status": "healthy", "helper": "Mean time to detect"},
                {"label": "Detection Rate", "value": "98.2%", "delta": "+0.7%", "status": "healthy", "helper": "Seeded AI scoring coverage"},
            ],
            "criticalQueue": sorted(deepcopy(list(incidents.values())), key=lambda item: item["riskScore"], reverse=True)[:4],
            "demoScenario": {
                "title": "Hybrid bootstrap-to-live SOC transition",
                "focusIncidentId": "BOOT-9101",
                "summary": "Seeded incidents load instantly, then hand over to live AI-backed telemetry without page refresh.",
            },
            "modelHealth": model_health,
        }

        metrics = {
            "severityDistribution": {
                "Critical": sum(1 for item in incidents.values() if item["severity"] == "Critical"),
                "High": sum(1 for item in incidents.values() if item["severity"] == "High"),
                "Medium": sum(1 for item in incidents.values() if item["severity"] == "Medium"),
                "Low": sum(1 for item in incidents.values() if item["severity"] == "Low"),
            },
            "recentActivity": deepcopy(events[:6]),
            "riskDistribution": [item["riskScore"] for item in incidents.values()],
            "spikeSummary": {
                "label": "Bootstrap anomaly wave",
                "window": "Last 10 minutes",
                "detail": "Seeded UEBA, phishing, credential, and lateral movement signals are warming the console while live pipelines attach.",
            },
            "kpis": {"MTTD": "06m", "MTTR": "18m", "detectionRate": "98.2%"},
        }

        return {
            "incidents": incidents,
            "events": events,
            "attackGraph": attack_graph,
            "overview": overview,
            "metrics": metrics,
            "detections": [
                {"id": "DET-BOOT-1", "source": "UEBA", "status": "Bootstrapping", "precision": 0.96, "drift": "Low", "lastUpdated": self._now_iso()},
                {"id": "DET-BOOT-2", "source": "Email AI", "status": "Healthy", "precision": 0.95, "drift": "Low", "lastUpdated": self._now_iso()},
                {"id": "DET-BOOT-3", "source": "URL AI", "status": "Healthy", "precision": 0.97, "drift": "Low", "lastUpdated": self._now_iso()},
                {"id": "DET-BOOT-4", "source": "Credential AI", "status": "High Activity", "precision": 0.93, "drift": "Low", "lastUpdated": self._now_iso()},
            ],
            "modelHealth": model_health,
            "streaming": {"counter": self._stream_counter, "mode": "bootstrap"},
        }

    def _tick_bootstrap_state(self) -> None:
        incidents = self._bootstrap_state["incidents"]
        if not incidents:
            return
        target = incidents[list(incidents.keys())[self._stream_counter % len(incidents)]]
        if self._stream_counter % 3 == 0 and target["severity"] != "Critical":
            target["severity"] = "Critical"
            target["riskScore"] = min(99, target["riskScore"] + 4)
            target["summary"]["severity"] = target["severity"]
        else:
            target["riskScore"] = min(99, target["riskScore"] + 1)
        target["updatedAt"] = self._now_iso()
        target["confidence"] = f"{min(0.99, float(target['confidence']) + 0.01):.2f}"
        target["summary"]["confidence"] = target["confidence"]
        event = {
            "id": f"BOOT-EVT-{5000 + self._stream_counter}",
            "incidentId": target["id"],
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "entity": target["entity"],
            "user": target["users"][0],
            "host": target["hosts"][0],
            "source": "UEBA" if self._stream_counter % 2 == 0 else "Attack Graph",
            "eventType": "streamed_risk_update" if self._stream_counter % 2 == 0 else "chain_confidence_increase",
            "severity": target["severity"],
            "score": target["riskScore"],
        }
        self._bootstrap_state["events"].insert(0, event)
        self._bootstrap_state["events"] = self._bootstrap_state["events"][:50]
        target["relatedAlerts"].insert(0, event)
        target["timeline"].append(
            {
                "time": datetime.now(timezone.utc).strftime("%H:%M"),
                "title": "Streamed detection update",
                "detail": f"Incident risk adjusted to {target['riskScore']} during bootstrap streaming.",
            }
        )
        if self._bootstrap_state["attackGraph"]["chains"]:
            chain = self._bootstrap_state["attackGraph"]["chains"][self._stream_counter % len(self._bootstrap_state["attackGraph"]["chains"])]
            chain["confidence"] = f"{min(0.99, float(chain['confidence']) + 0.01):.2f}"
            if target["severity"] == "Critical":
                chain["severity"] = "Critical"
        if self._bootstrap_state["attackGraph"]["nodes"]:
            node = self._bootstrap_state["attackGraph"]["nodes"][self._stream_counter % len(self._bootstrap_state["attackGraph"]["nodes"])]
            node["risk"] = "critical" if target["severity"] == "Critical" else node["risk"]
        self._bootstrap_state["streaming"] = {"counter": self._stream_counter, "mode": "bootstrap"}
        self._refresh_bootstrap_views()

    def _tick_live_state(self) -> None:
        if not self._incidents:
            return
        incident = self._incidents[list(self._incidents.keys())[self._stream_counter % len(self._incidents)]]
        incident["riskScore"] = min(99, incident["riskScore"] + (1 if self._stream_counter % 4 == 0 else 0))
        incident["updatedAt"] = self._now_iso()
        event = {
            "id": f"EVT-LIVE-{6000 + self._stream_counter}",
            "incidentId": incident["id"],
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "entity": incident["entity"],
            "user": incident["users"][0],
            "host": incident["hosts"][0],
            "source": "UEBA",
            "eventType": "live_detection_update",
            "severity": incident["severity"],
            "score": incident["riskScore"],
        }
        self._events.insert(0, event)
        self._events = self._events[:50]
        if self._attack_graph["chains"]:
            chain = self._attack_graph["chains"][self._stream_counter % len(self._attack_graph["chains"])]
            chain["confidence"] = f"{min(0.99, float(chain['confidence']) + 0.01):.2f}"
        self._attack_graph["riskLevels"] = [node["risk"] for node in self._attack_graph["nodes"]]

    def overview_mock(self) -> dict[str, Any]:
        return self.get_overview_summary()

    def incidents_mock(self) -> list[dict[str, Any]]:
        return self.list_incidents()

    def incident_detail_mock(self, incident_id: str | None = None) -> dict[str, Any]:
        if incident_id:
            incident = self.get_incident(incident_id)
            if incident is not None:
                return incident
        first = self.list_incidents()[0]["id"] if self.list_incidents() else None
        return self.get_incident(first) if first else {
            "summary": {"id": "INC-DEMO", "title": "Demo incident", "severity": "Medium", "confidence": "0.70", "status": "Open", "owner": "Unassigned", "users": [], "hosts": [], "mitre": []},
            "timeline": [],
            "evidence": [],
            "relatedAlerts": [],
        }

    def events_mock(self) -> list[dict[str, Any]]:
        return self.get_live_events()

    def graph_mock(self, incident_id: str | None = None) -> dict[str, Any]:
        return self.get_attack_graph(incident_id=incident_id)

    def reports_mock(self) -> list[dict[str, Any]]:
        return self.list_reports()

    def models_health_mock(self) -> list[dict[str, Any]]:
        return self.get_detection_feed()

    def detections_mock(self) -> list[dict[str, Any]]:
        return self.get_detection_feed()

    def investigations_mock(self, entity_id: str = "acct-payroll-09") -> dict[str, Any]:
        return self.get_investigation_entity(entity_id)

    def administration_mock(self) -> dict[str, Any]:
        return {
            "system": self.get_admin_system(),
            "users": self.get_admin_users(),
        }

    def detector_result_mock(self, detector: str) -> dict[str, Any]:
        base = {
            "email": {"phishing_probability": 0.82, "label": "phishing"},
            "url": {"phishing_probability": 0.91, "label": "phishing", "url": "http://example.test"},
            "credential": {"risk_score": 84, "matches": ["AKIAIOSFODNN7EXAMPLE"], "label": "credential_exposed"},
            "attachment": {"attachment_risk_score": 0.77, "malware_probability": 0.74},
            "prompt_guard": {"label": "safe", "blocked": False, "risk_score": 0.08},
        }
        return deepcopy(base.get(detector, {"label": "safe"}))

    def incident_report_mock(self) -> dict[str, Any]:
        incident = self.incident_detail_mock()
        return {
            "incident_id": incident["summary"]["id"],
            "title": incident["summary"]["title"],
            "severity": incident["summary"]["severity"],
            "confidence": incident["summary"]["confidence"],
            "executive_summary": "Credential misuse and privileged movement require containment and evidence preservation.",
            "recommended_actions": ["Contain impacted accounts", "Review graph pivots", "Prepare response playbook"],
        }

    def get_workflow_insight(self, view: str, incident_id: str | None = None) -> dict[str, Any]:
        normalized = view.strip().lower()
        default_incident = self.list_incidents()[0] if self.list_incidents() else None
        incident = self._incidents.get(incident_id) if incident_id else None
        incident = incident or default_incident

        insights: dict[str, dict[str, Any]] = {
            "overview": {
                "title": "Overview focus",
                "description": "Use the overview to confirm alert pressure, identify the most urgent incident, and hand off into triage with context intact.",
                "bullets": [
                    "Critical payroll and transfer activity currently dominate queue pressure.",
                    "UEBA, graph, and local SOC reasoning are all available for handoff.",
                    "Move next into monitoring or incident triage."
                ],
            },
            "monitoring": {
                "title": "Monitoring focus",
                "description": "Track event velocity, validate detector posture, and promote correlated activity into incident handling before it fragments.",
                "bullets": [
                    "Prioritize repeated credential and privilege signals.",
                    "High detector precision allows direct triage escalation for top events.",
                    "Move next into incidents once correlated activity is confirmed."
                ],
            },
            "incidents": {
                "title": "Triage focus",
                "description": "Use incident severity, SLA, and risk score together to decide which case should move into deeper investigation first.",
                "bullets": [
                    f"Current priority incident: {incident['id']}." if incident else "No priority incident currently selected.",
                    "Review timeline and MITRE mapping before escalation.",
                    "Move next into incident detail for evidence-backed decisions."
                ],
            },
            "investigations": {
                "title": "Investigation focus",
                "description": "Pivot on suspicious entities, validate supporting evidence, and narrow the likely attacker path before moving to the graph view.",
                "bullets": [
                    "Use entity activity frequency to isolate the strongest behavioral signal.",
                    "Cross-check user and host pivots against attack graph nodes.",
                    "Move next into the attack graph once the lead entity is confirmed."
                ],
            },
            "threat-graph": {
                "title": "Graph focus",
                "description": "Use the graph to confirm attacker movement, identify pivots, and determine whether containment should target accounts, hosts, or egress paths.",
                "bullets": [
                    "Critical chains currently converge on privileged identity and exfiltration nodes.",
                    "Sequence validation should precede playbook execution.",
                    "Move next into playbooks after chain confidence is confirmed."
                ],
            },
            "playbooks": {
                "title": "Response focus",
                "description": "Prepare containment and recovery steps only after evidence, timeline, and graph path are consistent with the selected incident.",
                "bullets": [
                    f"Primary response target: {incident['title']}." if incident else "Primary response target not selected.",
                    "Contain privileged access before restoring service workflows.",
                    "Move next into reports once execution is ready for analyst handoff."
                ],
            },
            "reports": {
                "title": "Reporting focus",
                "description": "Use reports to convert investigation evidence and response actions into a concise analyst handoff and executive summary.",
                "bullets": [
                    "Export the latest report after playbook preparation is complete.",
                    "Preserve incident severity and confidence in the handoff summary.",
                    "Return to overview after artifacts are ready."
                ],
            },
            "settings": {
                "title": "Administration focus",
                "description": "Review operator status, backend services, and user readiness without breaking the main SOC investigation flow.",
                "bullets": [
                    "Use this page to verify backend health before demos.",
                    "Administration should not interrupt active incident work.",
                    "Return to overview after system validation."
                ],
            },
        }

        if normalized == "incident-detail" and incident:
            return {
                "title": "Incident detail focus",
                "description": f"Validate {incident['id']} against timeline, evidence, and graph correlation before executing containment.",
                "bullets": [
                    "Confirm initiating access signal before escalation.",
                    "Check privileged asset exposure in the graph path.",
                    "Move next into investigation or playbook execution depending on evidence confidence."
                ],
            }

        return deepcopy(insights.get(normalized, insights["overview"]))

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
        timeline = [
            ("INC-21403", "jane.carter", "acct-payroll-09", "UEBA", "after_hours_login", "High", 86, 0),
            ("INC-21403", "svc-payroll-admin", "acct-payroll-09", "UEBA", "privilege_change", "Critical", 92, 3),
            ("INC-21403", "svc-payroll-admin", "dc-east-02", "UEBA", "lateral_move", "Critical", 95, 6),
            ("INC-21403", "svc-payroll-admin", "dc-east-02", "UEBA", "mass_file_access", "High", 84, 9),
            ("INC-21406", "svc-wire-transfer", "atm-cluster-02", "UEBA", "data_exfiltration", "Critical", 88, 12),
            ("INC-21404", "samir.khan", "teller-branch-11", "UEBA", "impossible_travel_login", "High", 78, 15),
            ("INC-21404", "samir.khan", "teller-branch-11", "Prompt Guard", "unknown_device", "High", 75, 18),
            ("INC-21405", "svc-underwrite", "loan-underwrite-03", "URL AI", "malware_signature", "High", 71, 21),
            ("INC-21405", "svc-underwrite", "loan-underwrite-03", "Email AI", "attachment_execution", "Medium", 69, 24),
            ("INC-21403", "jane.carter", "dc-east-02", "UEBA", "admin_token_request", "Critical", 91, 27),
            ("INC-21406", "svc-wire-transfer", "atm-cluster-02", "UEBA", "outbound_transfer_spike", "Critical", 90, 30),
            ("INC-21403", "svc-payroll-admin", "dc-east-02", "UEBA", "credential_rotation_failure", "High", 82, 33),
            ("INC-21404", "samir.khan", "teller-branch-11", "UEBA", "login_failed_burst", "Medium", 67, 36),
            ("INC-21406", "svc-wire-transfer", "atm-cluster-02", "Prompt Guard", "prompt_injection_attempt", "Medium", 64, 39),
        ]

        rows: list[dict[str, Any]] = []
        for index, (incident_id, user, host, source, event_type, severity, score, minutes_ago) in enumerate(timeline):
            rows.append(
                {
                    "id": f"EVT-{3100 + index}",
                    "incidentId": incident_id,
                    "timestamp": (base - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S"),
                    "entity": host or user,
                    "user": user,
                    "host": host,
                    "source": source,
                    "eventType": event_type,
                    "severity": severity,
                    "score": score,
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
            },
            {
                "id": "PLB-002",
                "name": "Exfiltration suppression",
                "steps": [
                    {"title": "Block egress", "detail": "Suppress outbound transfer paths and revoke exposed service tokens.", "owner": "Network Ops", "confidence": 94},
                    {"title": "Validate data scope", "detail": "Identify impacted systems and quantify data touched during the transfer spike.", "owner": "IR Lead", "confidence": 88},
                    {"title": "Restore trusted paths", "detail": "Re-enable approved transfer workflows after token rotation and validation.", "owner": "Platform Ops", "confidence": 84},
                ],
            },
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
            {"id": "U-005", "name": "Priya Sharma", "role": "Employee", "status": "Active"},
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

    def _refresh_bootstrap_views(self) -> None:
        incidents = list(self._bootstrap_state["incidents"].values())
        events = self._bootstrap_state["events"]
        self._bootstrap_state["overview"] = {
            "headline": {
                "title": "Enterprise SOC Overview",
                "subtitle": "Bootstrap intelligence is active while live AI mode initializes.",
                "status": "Live mode activating",
                "updatedAt": self._now_iso(),
            },
            "metrics": [
                {"label": "Active Incidents", "value": len(incidents), "delta": "+4", "status": "critical", "helper": "Bootstrap incident queue"},
                {"label": "Critical Incidents", "value": sum(1 for incident in incidents if incident["severity"] == "Critical"), "delta": "+1", "status": "critical", "helper": "Immediate analyst attention"},
                {"label": "MTTD", "value": "06m", "delta": "-1m", "status": "healthy", "helper": "Mean time to detect"},
                {"label": "Detection Rate", "value": "98.2%", "delta": "+0.7%", "status": "healthy", "helper": "Seeded AI scoring coverage"},
            ],
            "criticalQueue": sorted(deepcopy(incidents), key=lambda item: item["riskScore"], reverse=True)[:4],
            "demoScenario": {
                "title": "Hybrid bootstrap-to-live SOC transition",
                "focusIncidentId": sorted(incidents, key=lambda item: item["riskScore"], reverse=True)[0]["id"] if incidents else "BOOT-9101",
                "summary": "Seeded incidents load instantly, then hand over to live AI-backed telemetry without page refresh.",
            },
            "modelHealth": self._bootstrap_state["modelHealth"],
        }
        self._bootstrap_state["metrics"] = {
            "severityDistribution": {
                "Critical": sum(1 for item in incidents if item["severity"] == "Critical"),
                "High": sum(1 for item in incidents if item["severity"] == "High"),
                "Medium": sum(1 for item in incidents if item["severity"] == "Medium"),
                "Low": sum(1 for item in incidents if item["severity"] == "Low"),
            },
            "recentActivity": deepcopy(events[:6]),
            "riskDistribution": [item["riskScore"] for item in incidents],
            "spikeSummary": {
                "label": "Bootstrap anomaly wave",
                "window": "Last 10 minutes",
                "detail": "Seeded UEBA, phishing, credential, and lateral movement signals are warming the console while live pipelines attach.",
            },
            "kpis": {"MTTD": "06m", "MTTR": "18m", "detectionRate": "98.2%"},
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
