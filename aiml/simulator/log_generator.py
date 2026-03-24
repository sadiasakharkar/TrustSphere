"""Offline cybersecurity log simulator for TrustSphere AIML.

This module produces time-progressive enterprise telemetry with normal,
suspicious, and attack behavior distributions suitable for UEBA training.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from pathlib import Path
import random

import numpy as np
import pandas as pd


LOGGER = logging.getLogger(__name__)

RANDOM_SEED = 42
NORMAL_RATIO = 0.80
SUSPICIOUS_RATIO = 0.15
ATTACK_RATIO = 0.05

DEVICE_TYPES = ["corporate_laptop", "desktop", "thin_client", "vpn_tablet"]
LOCATIONS = ["Mumbai", "Pune", "Bengaluru", "Hyderabad", "Chennai", "Delhi"]
NORMAL_EVENTS = [
    "login",
    "file_access",
    "email_send",
    "database_query",
    "internal_app_use",
    "logout",
]
SUSPICIOUS_EVENTS = [
    "after_hours_login",
    "large_file_download",
    "vpn_ip_change",
    "credential_retry",
]
ATTACK_EVENTS = [
    "brute_force_login",
    "data_exfiltration",
    "impossible_travel",
    "privilege_escalation",
]
PROCESS_NAMES = [
    "outlook.exe",
    "chrome.exe",
    "teams.exe",
    "excel.exe",
    "powershell.exe",
    "svchost.exe",
    "sqlclient.exe",
]
ATTACK_PROCESSES = [
    "mimikatz.exe",
    "rclone.exe",
    "powershell.exe",
    "psexec.exe",
]


@dataclass(slots=True)
class UserBehavior:
    """Persistent behavioral baseline for a simulated enterprise user."""

    user_id: str
    base_ip: str
    base_location: str
    device_type: str
    start_hour: int
    end_hour: int
    average_bytes_sent: int
    average_bytes_received: int


def generate_logs(
    output_path: str | Path | None = None,
    n_users: int = 250,
    n_days: int = 7,
    seed: int = RANDOM_SEED,
) -> Path:
    """Generate offline training logs and persist them to CSV."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    if output_path is None:
        output_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "logs.csv"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    users = _create_user_population(n_users, rng)
    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=n_days)
    records: list[dict] = []

    for day_offset in range(n_days):
        current_day = start_time + timedelta(days=day_offset)
        for user in users:
            daily_event_count = rng.randint(18, 40)
            time_cursor = current_day + timedelta(hours=user.start_hour, minutes=rng.randint(0, 25))

            for _ in range(daily_event_count):
                behavior_label = _sample_behavior_label(rng)
                event = _build_event(user, time_cursor, behavior_label, rng, np_rng)
                records.append(event)
                time_cursor += timedelta(minutes=rng.randint(4, 40))

    frame = pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)
    frame.to_csv(output_path, index=False)
    LOGGER.info("Generated %s logs at %s", len(frame), output_path)
    return output_path


def _create_user_population(n_users: int, rng: random.Random) -> list[UserBehavior]:
    users: list[UserBehavior] = []
    for index in range(n_users):
        users.append(
            UserBehavior(
                user_id=f"user_{index:05d}",
                base_ip=_random_ip(rng, private=True),
                base_location=rng.choice(LOCATIONS),
                device_type=rng.choice(DEVICE_TYPES[:3]),
                start_hour=rng.randint(7, 10),
                end_hour=rng.randint(17, 20),
                average_bytes_sent=rng.randint(1_500, 40_000),
                average_bytes_received=rng.randint(2_000, 80_000),
            )
        )
    return users


def _sample_behavior_label(rng: random.Random) -> str:
    draw = rng.random()
    if draw < NORMAL_RATIO:
        return "normal"
    if draw < NORMAL_RATIO + SUSPICIOUS_RATIO:
        return "suspicious"
    return "attack"


def _build_event(
    user: UserBehavior,
    timestamp: datetime,
    behavior_label: str,
    rng: random.Random,
    np_rng: np.random.Generator,
) -> dict:
    if behavior_label == "normal":
        return _normal_event(user, timestamp, rng, np_rng)
    if behavior_label == "suspicious":
        return _suspicious_event(user, timestamp, rng, np_rng)
    return _attack_event(user, timestamp, rng, np_rng)


def _normal_event(
    user: UserBehavior,
    timestamp: datetime,
    rng: random.Random,
    np_rng: np.random.Generator,
) -> dict:
    event_type = rng.choice(NORMAL_EVENTS)
    bytes_sent = max(0, int(np_rng.normal(user.average_bytes_sent, user.average_bytes_sent * 0.25)))
    bytes_received = max(
        0,
        int(np_rng.normal(user.average_bytes_received, user.average_bytes_received * 0.30)),
    )
    login_success = 1 if event_type == "login" else 1
    failed_attempts = 0
    process_name = rng.choice(PROCESS_NAMES)
    return {
        "timestamp": timestamp.isoformat(),
        "user_id": user.user_id,
        "ip_address": user.base_ip,
        "event_type": event_type,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received,
        "login_success": login_success,
        "device_type": user.device_type,
        "location": user.base_location,
        "process_name": process_name,
        "failed_attempts": failed_attempts,
    }


def _suspicious_event(
    user: UserBehavior,
    timestamp: datetime,
    rng: random.Random,
    np_rng: np.random.Generator,
) -> dict:
    anomaly_type = rng.choice(SUSPICIOUS_EVENTS)
    if anomaly_type == "after_hours_login":
        timestamp = timestamp.replace(hour=rng.choice([1, 2, 3, 4, 22, 23]), minute=rng.randint(0, 59))
        login_success = 1
        failed_attempts = rng.randint(1, 2)
    elif anomaly_type == "credential_retry":
        login_success = 0
        failed_attempts = rng.randint(3, 8)
    else:
        login_success = 1
        failed_attempts = rng.randint(0, 2)

    if anomaly_type == "large_file_download":
        bytes_sent = max(0, int(np_rng.normal(user.average_bytes_sent * 1.8, user.average_bytes_sent * 0.4)))
        bytes_received = max(
            0,
            int(np_rng.normal(user.average_bytes_received * 4.5, user.average_bytes_received * 0.6)),
        )
        process_name = "chrome.exe"
    else:
        bytes_sent = max(0, int(np_rng.normal(user.average_bytes_sent * 1.3, user.average_bytes_sent * 0.35)))
        bytes_received = max(
            0,
            int(np_rng.normal(user.average_bytes_received * 1.7, user.average_bytes_received * 0.4)),
        )
        process_name = rng.choice(PROCESS_NAMES)

    ip_address = _random_ip(rng, private=False) if anomaly_type == "vpn_ip_change" else user.base_ip
    location = rng.choice([loc for loc in LOCATIONS if loc != user.base_location]) if anomaly_type == "vpn_ip_change" else user.base_location
    device_type = "unknown_device" if anomaly_type == "credential_retry" else user.device_type

    return {
        "timestamp": timestamp.isoformat(),
        "user_id": user.user_id,
        "ip_address": ip_address,
        "event_type": anomaly_type,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received,
        "login_success": login_success,
        "device_type": device_type,
        "location": location,
        "process_name": process_name,
        "failed_attempts": failed_attempts,
    }


def _attack_event(
    user: UserBehavior,
    timestamp: datetime,
    rng: random.Random,
    np_rng: np.random.Generator,
) -> dict:
    attack_type = rng.choice(ATTACK_EVENTS)
    if attack_type == "brute_force_login":
        login_success = 0
        failed_attempts = rng.randint(8, 20)
        bytes_sent = max(0, int(np_rng.normal(1_500, 400)))
        bytes_received = max(0, int(np_rng.normal(1_200, 300)))
        ip_address = _random_ip(rng, private=False)
        location = rng.choice([loc for loc in LOCATIONS if loc != user.base_location])
        process_name = "powershell.exe"
    elif attack_type == "data_exfiltration":
        login_success = 1
        failed_attempts = rng.randint(0, 1)
        bytes_sent = max(0, int(np_rng.normal(user.average_bytes_sent * 12, user.average_bytes_sent * 2)))
        bytes_received = max(0, int(np_rng.normal(user.average_bytes_received * 0.7, user.average_bytes_received * 0.15)))
        ip_address = _random_ip(rng, private=False)
        location = user.base_location
        process_name = "rclone.exe"
    elif attack_type == "impossible_travel":
        login_success = 1
        failed_attempts = rng.randint(1, 3)
        bytes_sent = max(0, int(np_rng.normal(user.average_bytes_sent * 1.6, user.average_bytes_sent * 0.4)))
        bytes_received = max(0, int(np_rng.normal(user.average_bytes_received * 1.4, user.average_bytes_received * 0.3)))
        ip_address = _random_ip(rng, private=False)
        location = rng.choice([loc for loc in LOCATIONS if loc != user.base_location])
        process_name = rng.choice(ATTACK_PROCESSES)
    else:
        login_success = 1
        failed_attempts = rng.randint(0, 2)
        bytes_sent = max(0, int(np_rng.normal(user.average_bytes_sent * 2.5, user.average_bytes_sent * 0.5)))
        bytes_received = max(0, int(np_rng.normal(user.average_bytes_received * 2.0, user.average_bytes_received * 0.5)))
        ip_address = _random_ip(rng, private=False)
        location = user.base_location
        process_name = "mimikatz.exe"

    return {
        "timestamp": timestamp.isoformat(),
        "user_id": user.user_id,
        "ip_address": ip_address,
        "event_type": attack_type,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received,
        "login_success": login_success,
        "device_type": "attacker_device",
        "location": location,
        "process_name": process_name,
        "failed_attempts": failed_attempts,
    }


def _random_ip(rng: random.Random, private: bool) -> str:
    if private:
        return f"10.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    return ".".join(str(rng.randint(1, 254)) for _ in range(4))
