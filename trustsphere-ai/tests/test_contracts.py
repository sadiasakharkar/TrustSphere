from __future__ import annotations

import unittest

from src.contracts import (
    EMAIL_REQUEST_SCHEMA_VERSION,
    INCIDENT_SCHEMA_VERSION,
    EmailDetectionRequest,
    IncidentAnalysisRequest,
    NormalizedEvent,
)
from src.pipeline.event_normalizer import EventNormalizer


class ContractRegistryTests(unittest.TestCase):
    def test_normalized_event_has_canonical_schema_version(self) -> None:
        event = NormalizedEvent.model_validate(
            {
                "timestamp": "2026-03-24T08:00:00Z",
                "user": "alice",
                "host": "host-1",
                "ip": "10.0.0.1",
                "event_type": "login_success",
            }
        )
        self.assertEqual(event.schema_version, "event.v1")

    def test_event_normalizer_maps_aliases_into_canonical_fields(self) -> None:
        normalizer = EventNormalizer()
        events = normalizer.normalize(
            {
                "timestamp": "2026-03-24T08:00:00Z",
                "user": "alice",
                "device": "endpoint-7",
                "ip_address": "10.10.10.10",
                "event_type": "file_access",
                "command": "powershell.exe",
                "content_text": "AWS_SECRET_ACCESS_KEY=test",
            }
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].host, "endpoint-7")
        self.assertEqual(events[0].ip, "10.10.10.10")
        self.assertEqual(events[0].process_name, "powershell.exe")
        self.assertEqual(events[0].text_content, "AWS_SECRET_ACCESS_KEY=test")

    def test_request_schemas_are_versioned(self) -> None:
        email_request = EmailDetectionRequest.model_validate({"schema_version": EMAIL_REQUEST_SCHEMA_VERSION, "email_text": "test"})
        incident_request = IncidentAnalysisRequest.model_validate({"schema_version": INCIDENT_SCHEMA_VERSION, "logs": []})
        self.assertEqual(email_request.schema_version, EMAIL_REQUEST_SCHEMA_VERSION)
        self.assertEqual(incident_request.schema_version, INCIDENT_SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
