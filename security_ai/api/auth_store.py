from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import secrets
from threading import RLock
from typing import Any
from uuid import uuid4


STORE_PATH = Path(__file__).resolve().parent / "data" / "auth_users.json"
_LOCK = RLock()


def _ensure_store() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        STORE_PATH.write_text("[]", encoding="utf-8")


def _read_users() -> list[dict[str, Any]]:
    _ensure_store()
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        STORE_PATH.write_text("[]", encoding="utf-8")
        return []


def _write_users(users: list[dict[str, Any]]) -> None:
    _ensure_store()
    STORE_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def _normalize_role(role: str) -> str:
    normalized = str(role or "analyst").lower().strip()
    if normalized in {"admin", "analyst", "employee"}:
        return normalized
    return "analyst"


def _hash_password(password: str, salt: str | None = None) -> str:
    resolved_salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), resolved_salt.encode("utf-8"), 120000)
    return f"{resolved_salt}${derived.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, _ = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)


def sanitize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "createdAt": user["createdAt"],
    }


def create_user(name: str, email: str, password: str, role: str) -> dict[str, Any]:
    normalized_email = str(email or "").lower().strip()
    normalized_name = str(name or "").strip()
    normalized_role = _normalize_role(role)
    if not normalized_name or not normalized_email or not password:
        raise ValueError("Name, email, password, and role are required.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")

    with _LOCK:
        users = _read_users()
        if any(user["email"] == normalized_email for user in users):
            raise ValueError("A user with this email already exists.")

        now = datetime.now(timezone.utc).isoformat()
        user = {
            "id": str(uuid4()),
            "name": normalized_name,
            "email": normalized_email,
            "role": normalized_role,
            "passwordHash": _hash_password(password),
            "createdAt": now,
        }
        users.append(user)
        _write_users(users)
        return sanitize_user(user)


def authenticate_user(email: str, password: str) -> dict[str, Any]:
    normalized_email = str(email or "").lower().strip()
    with _LOCK:
        users = _read_users()
        user = next((row for row in users if row["email"] == normalized_email), None)
    if user is None:
        raise LookupError("User not found. Please register yourself first.")
    if not _verify_password(password, user.get("passwordHash", "")):
        raise PermissionError("Invalid email or password.")
    return sanitize_user(user)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    normalized_email = str(email or "").lower().strip()
    with _LOCK:
        users = _read_users()
        user = next((row for row in users if row["email"] == normalized_email), None)
    return sanitize_user(user) if user else None
