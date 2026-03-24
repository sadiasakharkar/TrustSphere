"""Enterprise-grade behavioral log simulator for TrustSphere AI.

This module simulates realistic enterprise telemetry for UEBA, anomaly detection,
attack graph reconstruction, and response reasoning workflows. The design favors
behavioral consistency, temporal realism, and causal attack chains instead of
flat random event generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path
import random
import uuid

from faker import Faker

fake = Faker()


ROLE_DEPARTMENTS = {
    "employee": ["operations", "hr", "sales", "support"],
    "developer": ["engineering", "platform", "security-engineering"],
    "admin": ["it-operations", "identity", "infrastructure"],
    "finance": ["treasury", "payments", "audit", "accounting"],
}

ROLE_SYSTEMS = {
    "employee": ["hr_portal", "crm", "email", "shared_drive"],
    "developer": ["gitlab", "build_runner", "kubernetes", "artifact_repo"],
    "admin": ["iam_console", "vpn_gateway", "server_manager", "siem_console"],
    "finance": ["payments_core", "ledger_system", "regulatory_reports", "email"],
}

EVENT_SOURCE_BY_TYPE = {
    "login_success": "IAM",
    "logout": "IAM",
    "vpn_connect": "Firewall",
    "email_send": "Email",
    "email_read": "Email",
    "file_access": "EDR",
    "file_download": "EDR",
    "system_usage": "EDR",
    "process_execution": "EDR",
    "admin_console_access": "IAM",
    "db_query": "EDR",
    "login_after_hours": "IAM",
    "login_from_new_ip": "Firewall",
    "unknown_device_login": "EDR",
    "mass_file_access": "EDR",
    "phishing_email": "Email",
    "privilege_escalation": "IAM",
    "lateral_movement": "EDR",
    "data_exfiltration": "Firewall",
}

SEVERITY_BY_LABEL = {
    "normal": "low",
    "suspicious": "medium",
    "attack": "high",
}


@dataclass(slots=True)
class UserProfile:
    """Persistent behavioral profile representing a real enterprise user."""

    username: str
    role: str
    department: str
    assigned_devices: list[str]
    baseline_login_hour: int
    baseline_logout_hour: int
    baseline_ip: str
    baseline_location: str
    behavior_consistency_score: float
    daily_event_band: tuple[int, int]
    preferred_systems: list[str] = field(default_factory=list)


class BehaviorEngine:
    """Generates normal and suspicious events while honoring user baselines."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def build_normal_day(
        self,
        user: UserProfile,
        day_start: datetime,
        session_index: int,
    ) -> list[dict]:
        """Simulate a realistic workday with role-aware activity patterns."""
        events: list[dict] = []
        session_id = self._make_session_id(user, day_start, session_index)
        login_at = self._baseline_login_time(user, day_start)
        logout_at = self._baseline_logout_time(user, login_at)
        device = self.rng.choice(user.assigned_devices)

        events.append(
            self._event(
                timestamp=login_at,
                user=user,
                session_id=session_id,
                event_type="login_success",
                event_category="authentication",
                ip=user.baseline_ip,
                device=device,
                label="normal",
                risk_hint="baseline_login_pattern",
            )
        )

        current_time = login_at + timedelta(minutes=self.rng.randint(8, 20))
        target_event_count = self.rng.randint(*user.daily_event_band)
        core_actions = max(4, target_event_count - 2)

        for _ in range(core_actions):
            event_type, category = self._normal_event_for_role(user.role)
            current_time += timedelta(minutes=self.rng.randint(4, 35))
            if current_time >= logout_at - timedelta(minutes=12):
                break
            events.append(
                self._event(
                    timestamp=current_time,
                    user=user,
                    session_id=session_id,
                    event_type=event_type,
                    event_category=category,
                    ip=user.baseline_ip,
                    device=device,
                    label="normal",
                    risk_hint="baseline_usage_pattern",
                )
            )

        events.append(
            self._event(
                timestamp=logout_at,
                user=user,
                session_id=session_id,
                event_type="logout",
                event_category="session",
                ip=user.baseline_ip,
                device=device,
                label="normal",
                risk_hint="baseline_logout_pattern",
            )
        )
        return events

    def build_suspicious_event(
        self,
        user: UserProfile,
        day_start: datetime,
        sequence_index: int,
    ) -> dict:
        """Generate a plausible anomaly by violating at least one baseline."""
        session_id = self._make_session_id(user, day_start, sequence_index, prefix="susp")
        anomaly_type = self.rng.choice(
            ["after_hours_login", "ip_switch", "mass_file_access", "unknown_device"]
        )

        if anomaly_type == "after_hours_login":
            timestamp = day_start + timedelta(hours=self.rng.choice([1, 2, 3, 4, 23]))
            return self._event(
                timestamp=timestamp,
                user=user,
                session_id=session_id,
                event_type="login_after_hours",
                event_category="authentication",
                ip=user.baseline_ip,
                device=self.rng.choice(user.assigned_devices),
                label="suspicious",
                risk_hint="login_outside_baseline_hours",
            )

        if anomaly_type == "ip_switch":
            timestamp = day_start + timedelta(hours=user.baseline_login_hour, minutes=15)
            return self._event(
                timestamp=timestamp,
                user=user,
                session_id=session_id,
                event_type="login_from_new_ip",
                event_category="network",
                ip=fake.ipv4_public(),
                device=self.rng.choice(user.assigned_devices),
                label="suspicious",
                risk_hint=f"geo_anomaly_from_{user.baseline_location}",
            )

        if anomaly_type == "mass_file_access":
            timestamp = day_start + timedelta(hours=user.baseline_login_hour + 1, minutes=30)
            return self._event(
                timestamp=timestamp,
                user=user,
                session_id=session_id,
                event_type="mass_file_access",
                event_category="data_access",
                ip=user.baseline_ip,
                device=self.rng.choice(user.assigned_devices),
                label="suspicious",
                risk_hint="file_access_volume_above_role_baseline",
            )

        timestamp = day_start + timedelta(hours=user.baseline_login_hour, minutes=8)
        return self._event(
            timestamp=timestamp,
            user=user,
            session_id=session_id,
            event_type="unknown_device_login",
            event_category="endpoint",
            ip=user.baseline_ip,
            device="unmanaged_endpoint",
            label="suspicious",
            risk_hint="device_not_seen_in_baseline",
        )

    def _baseline_login_time(self, user: UserProfile, day_start: datetime) -> datetime:
        minute_jitter = self.rng.randint(0, max(5, int(60 * (1.0 - user.behavior_consistency_score))))
        return day_start + timedelta(hours=user.baseline_login_hour, minutes=minute_jitter)

    def _baseline_logout_time(self, user: UserProfile, login_time: datetime) -> datetime:
        base_duration = user.baseline_logout_hour - user.baseline_login_hour
        duration_hours = max(6, base_duration + self.rng.randint(-1, 1))
        return login_time + timedelta(hours=duration_hours, minutes=self.rng.randint(0, 25))

    def _normal_event_for_role(self, role: str) -> tuple[str, str]:
        role_events = {
            "employee": [
                ("email_read", "communication"),
                ("email_send", "communication"),
                ("file_access", "data_access"),
                ("system_usage", "application"),
            ],
            "developer": [
                ("process_execution", "endpoint"),
                ("file_access", "data_access"),
                ("system_usage", "application"),
                ("db_query", "application"),
            ],
            "admin": [
                ("admin_console_access", "privileged_access"),
                ("system_usage", "application"),
                ("process_execution", "endpoint"),
                ("vpn_connect", "network"),
            ],
            "finance": [
                ("file_access", "data_access"),
                ("db_query", "application"),
                ("email_send", "communication"),
                ("system_usage", "application"),
            ],
        }
        return self.rng.choice(role_events[role])

    def _event(
        self,
        timestamp: datetime,
        user: UserProfile,
        session_id: str,
        event_type: str,
        event_category: str,
        ip: str,
        device: str,
        label: str,
        risk_hint: str | None = None,
    ) -> dict:
        return {
            "timestamp": timestamp.isoformat(),
            "user": user.username,
            "role": user.role,
            "department": user.department,
            "ip": ip,
            "device": device,
            "event_type": event_type,
            "event_category": event_category,
            "event_source": EVENT_SOURCE_BY_TYPE.get(event_type, "EDR"),
            "session_id": session_id,
            "severity_hint": self._severity_hint(event_type, label),
            "risk_hint": risk_hint,
            "label": label,
        }

    def _make_session_id(
        self,
        user: UserProfile,
        day_start: datetime,
        sequence_index: int,
        prefix: str = "sess",
    ) -> str:
        return f"{prefix}-{user.username}-{day_start.strftime('%Y%m%d')}-{sequence_index:03d}"

    def _severity_hint(self, event_type: str, label: str) -> str:
        if event_type in {"privilege_escalation", "data_exfiltration"}:
            return "critical"
        if event_type in {"lateral_movement", "login_from_new_ip", "mass_file_access"}:
            return "high"
        return SEVERITY_BY_LABEL[label]


class AttackInjector:
    """Injects causally linked multi-step attack chains."""

    def __init__(self, rng: random.Random, behavior_engine: BehaviorEngine) -> None:
        self.rng = rng
        self.behavior_engine = behavior_engine

    def credential_compromise_chain(
        self,
        user: UserProfile,
        day_start: datetime,
        chain_index: int,
    ) -> list[dict]:
        """Generate a realistic credential compromise chain."""
        session_id = f"attack-{user.username}-{day_start.strftime('%Y%m%d')}-{chain_index:03d}"
        attacker_ip = fake.ipv4_public()
        attacker_device = "attacker_workstation"
        base_time = day_start + timedelta(hours=self.rng.randint(7, 19), minutes=self.rng.randint(0, 59))
        event_specs = [
            ("phishing_email", "email", "spearphishing_delivery_detected"),
            ("login_from_new_ip", "network", f"new_ip_not_matching_{user.baseline_location}"),
            ("privilege_escalation", "privileged_access", "abnormal_privilege_grant_sequence"),
            ("lateral_movement", "lateral_movement", "cross_host_remote_execution_pattern"),
            ("data_exfiltration", "exfiltration", "high_volume_outbound_transfer"),
        ]

        logs: list[dict] = []
        current_time = base_time
        for index, (event_type, category, risk_hint) in enumerate(event_specs):
            current_time += timedelta(minutes=self.rng.randint(3, 18) if index else 0)
            logs.append(
                self.behavior_engine._event(
                    timestamp=current_time,
                    user=user,
                    session_id=session_id,
                    event_type=event_type,
                    event_category=category,
                    ip=attacker_ip if index else user.baseline_ip,
                    device=attacker_device if index else self.rng.choice(user.assigned_devices),
                    label="attack",
                    risk_hint=risk_hint,
                )
            )
        return logs


class LogGenerator:
    """Coordinates user modeling, behavior generation, and attack injection."""

    def __init__(
        self,
        n_users: int = 100,
        days: int = 1,
        suspicious_rate: float = 0.18,
        attack_rate: float = 0.04,
        seed: int = 42,
    ) -> None:
        self.n_users = n_users
        self.days = days
        self.suspicious_rate = suspicious_rate
        self.attack_rate = attack_rate
        self.rng = random.Random(seed)
        Faker.seed(seed)
        self.behavior_engine = BehaviorEngine(self.rng)
        self.attack_injector = AttackInjector(self.rng, self.behavior_engine)

    def create_users(self) -> list[UserProfile]:
        """Create persistent enterprise user profiles."""
        roles = ["employee", "developer", "admin", "finance"]
        users: list[UserProfile] = []

        for _ in range(self.n_users):
            role = self.rng.choices(roles, weights=[0.55, 0.2, 0.1, 0.15], k=1)[0]
            department = self.rng.choice(ROLE_DEPARTMENTS[role])
            consistency = round(self.rng.uniform(0.72, 0.97), 2)
            device_count = 2 if role in {"developer", "admin"} and self.rng.random() < 0.45 else 1
            devices = [self._device_name(role, idx) for idx in range(device_count)]
            login_hour = self.rng.randint(7, 10) if role != "admin" else self.rng.randint(6, 9)
            logout_hour = login_hour + self.rng.randint(8, 10)
            users.append(
                UserProfile(
                    username=fake.user_name(),
                    role=role,
                    department=department,
                    assigned_devices=devices,
                    baseline_login_hour=login_hour,
                    baseline_logout_hour=logout_hour,
                    baseline_ip=fake.ipv4_private(),
                    baseline_location=self.rng.choice(
                        ["Mumbai", "Pune", "Bengaluru", "Hyderabad", "Chennai", "Delhi"]
                    ),
                    behavior_consistency_score=consistency,
                    daily_event_band=self._daily_event_band(role),
                    preferred_systems=ROLE_SYSTEMS[role],
                )
            )
        return users

    def generate(self) -> list[dict]:
        """Generate chronologically ordered logs over a multi-day window."""
        users = self.create_users()
        logs: list[dict] = []
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for day_offset in range(self.days):
            day_start = start_date + timedelta(days=day_offset)
            for user_index, user in enumerate(users):
                daily_logs = self.behavior_engine.build_normal_day(user, day_start, user_index)
                logs.extend(daily_logs)

                # Suspicious activity frequency is role-aware and consistency-aware.
                anomaly_probability = self.suspicious_rate + max(0.0, (0.82 - user.behavior_consistency_score) * 0.2)
                if self.rng.random() < anomaly_probability:
                    logs.append(
                        self.behavior_engine.build_suspicious_event(user, day_start, user_index)
                    )

                # Attack chains stay rare and are more valuable than noise.
                attack_probability = self.attack_rate if user.role != "admin" else self.attack_rate * 1.35
                if self.rng.random() < attack_probability:
                    logs.extend(
                        self.attack_injector.credential_compromise_chain(user, day_start, user_index)
                    )

        logs.sort(key=lambda event: event["timestamp"])
        return logs

    def _daily_event_band(self, role: str) -> tuple[int, int]:
        return {
            "employee": (18, 28),
            "developer": (25, 40),
            "admin": (22, 36),
            "finance": (20, 32),
        }[role]

    def _device_name(self, role: str, index: int) -> str:
        prefix = {
            "employee": "corp-laptop",
            "developer": "dev-workstation",
            "admin": "admin-console",
            "finance": "fin-terminal",
        }[role]
        return f"{prefix}-{index + 1}"


def save_logs(
    n_users: int = 100,
    days: int = 1,
    output_path: Path | None = None,
) -> Path:
    """Generate and persist structured enterprise logs as JSON."""
    generator = LogGenerator(n_users=n_users, days=days)
    logs = generator.generate()
    if output_path is None:
        output_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "enterprise_logs.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(logs, handle, indent=2)
    print(f"Enterprise logs generated: {len(logs)} -> {output_path}")
    return output_path


if __name__ == "__main__":
    save_logs()
