"""Attack graph generation placeholder."""


def build_attack_graph(event_bundle: dict) -> dict:
    return {
        "nodes": ["phishing", "credential_access", "lateral_movement"],
        "edges": [["phishing", "credential_access"], ["credential_access", "lateral_movement"]],
        "context": event_bundle,
    }
