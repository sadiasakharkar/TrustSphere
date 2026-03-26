import json
from pathlib import Path

FILE = Path(__file__).resolve().parent / "history.json"


def save_history(entry):
    data = get_history()
    data.append(entry)
    FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_history():
    if not FILE.exists():
        return []
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def clear_history():
    FILE.write_text("[]", encoding="utf-8")
