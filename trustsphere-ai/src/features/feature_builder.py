"""Feature engineering entry points."""


def build_features(event: dict) -> dict:
    """Construct simple placeholder features from a normalized event."""
    return {
        "source": event.get("source", "unknown"),
        "normalized": event.get("normalized", False),
        "feature_count": len(event),
    }
