"""Detector adapters for unified TrustSphere orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

from ..contracts import DetectorFinding, DetectorFindingBatch, NormalizedEvent

BASE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BASE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from security_ai.detect_credentials import CredentialExposurePredictor
from security_ai.predict_attachment import AttachmentPredictor
from security_ai.predict_email import EmailPredictor
from security_ai.predict_url import URLPhishingPredictor
from security_ai.prompt_guard import PromptInjectionGuard


class UnifiedDetectorAdapter:
    """Run existing security_ai detectors against canonical normalized events."""

    def __init__(self) -> None:
        self._email_predictor: EmailPredictor | None = None
        self._url_predictor: URLPhishingPredictor | None = None
        self._credential_predictor: CredentialExposurePredictor | None = None
        self._attachment_predictor: AttachmentPredictor | None = None
        self._prompt_guard: PromptInjectionGuard | None = None

    def detect(self, events: list[NormalizedEvent]) -> DetectorFindingBatch:
        findings: list[DetectorFinding] = []
        for event in events:
            findings.extend(self._email_findings(event))
            findings.extend(self._url_findings(event))
            findings.extend(self._credential_findings(event))
            findings.extend(self._attachment_findings(event))
            findings.extend(self._prompt_findings(event))
        return DetectorFindingBatch(findings=findings)

    def _email_findings(self, event: NormalizedEvent) -> list[DetectorFinding]:
        if not (event.email_subject or event.email_body):
            return []
        predictor = self._email_predictor or EmailPredictor()
        self._email_predictor = predictor
        result = predictor.predict(event.email_subject or "", event.email_body or "", event.sender or f"{event.user}@local", event.attachment_name or "")
        if result.get("phishing_probability", 0.0) < 0.5:
            return []
        return [self._finding(event, "email_detector", "phishing_email", result, [f"phishing_probability={result['phishing_probability']:.4f}"])]

    def _url_findings(self, event: NormalizedEvent) -> list[DetectorFinding]:
        if not event.url:
            return []
        predictor = self._url_predictor or URLPhishingPredictor()
        self._url_predictor = predictor
        result = predictor.predict(event.url)
        if result.get("phishing_probability", 0.0) < 0.5:
            return []
        return [self._finding(event, "url_detector", "phishing_url", result, [event.url])]

    def _credential_findings(self, event: NormalizedEvent) -> list[DetectorFinding]:
        if not event.text_content:
            return []
        predictor = self._credential_predictor or CredentialExposurePredictor()
        self._credential_predictor = predictor
        result = predictor.predict(event.text_content, paste_context=event.event_type)
        if not result.get("credential_exposed"):
            return []
        return [self._finding(event, "credential_detector", "credential_exposure", result, [f"risk_score={result['risk_score']}"])]

    def _attachment_findings(self, event: NormalizedEvent) -> list[DetectorFinding]:
        if not event.attachment_name:
            return []
        predictor = self._attachment_predictor or AttachmentPredictor()
        self._attachment_predictor = predictor
        result = predictor.predict(
            event.attachment_name,
            int(event.attachment_size_bytes or 0),
            event.text_content or "",
            event.event_type,
            event.post_download_action or "",
        )
        if result.get("malware_probability", 0.0) < 0.5:
            return []
        return [self._finding(event, "attachment_detector", "malicious_attachment", result, [event.attachment_name])]

    def _prompt_findings(self, event: NormalizedEvent) -> list[DetectorFinding]:
        if not event.prompt_text:
            return []
        guard = self._prompt_guard or PromptInjectionGuard()
        self._prompt_guard = guard
        result = guard.evaluate(event.prompt_text)
        if not result.get("blocked"):
            return []
        evidence = list(result.get("matched_rules", [])) or ["prompt classified as injection"]
        return [self._finding(event, "prompt_guard", "prompt_injection", result, evidence)]

    def _finding(self, event: NormalizedEvent, detector_name: str, finding_type: str, result: dict[str, Any], evidence: list[str]) -> DetectorFinding:
        confidence = max(
            float(result.get("phishing_probability", 0.0)),
            float(result.get("probability", 0.0)),
            float(result.get("malware_probability", 0.0)),
            float(result.get("injection_probability", 0.0)),
            0.5,
        )
        severity = "CRITICAL" if confidence >= 0.9 else "HIGH" if confidence >= 0.75 else "MEDIUM"
        return DetectorFinding(
            detector_name=detector_name,
            entity_id=event.user,
            timestamp=event.timestamp if isinstance(event.timestamp, datetime) else datetime.now(timezone.utc),
            finding_type=finding_type,
            severity=severity,
            confidence=min(max(confidence, 0.0), 1.0),
            evidence=evidence,
            raw_output=result,
        )
