"""Feature engineering for phishing email detection."""

from __future__ import annotations

from dataclasses import dataclass
import html
import logging
import math
import re
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
SIGNATURE_PATTERN = re.compile(r"(?im)(^--\s*$|^best regards,.*|^thanks,.*|^sent from my .*|^kind regards,.*)")
REPLY_CHAIN_PATTERN = re.compile(r"(?ims)(from:.*?sent:.*?subject:.*$)")
URGENCY_KEYWORDS = {"urgent", "immediately", "action required", "verify", "suspend", "alert", "asap", "reset"}
FINANCIAL_TERMS = {"invoice", "payment", "wire", "bank", "account", "statement", "fund", "transfer"}
IMPERSONATION_TERMS = {"ceo", "cfo", "hr", "it support", "security team", "administrator", "helpdesk"}


@dataclass(slots=True)
class FeatureArtifacts:
    dataframe: pd.DataFrame
    metadata_columns: list[str]
    feature_columns: list[str]


class PhishingEmailFeatureEngineer:
    """Clean phishing email data and build text and metadata features."""

    def prepare_dataset(self, dataframes: list[pd.DataFrame]) -> pd.DataFrame:
        if not dataframes:
            return self._build_mock_dataset()
        combined = pd.concat(dataframes, ignore_index=True)
        combined.columns = [str(column).strip().lower() for column in combined.columns]
        rename_map = {
            "body": "email_body",
            "text": "email_body",
            "content": "email_body",
            "subject_line": "subject",
            "from": "sender",
            "sender_email": "sender",
            "label": "label",
        }
        combined = combined.rename(columns=rename_map)
        if "email_body" not in combined.columns:
            combined["email_body"] = ""
        if "subject" not in combined.columns:
            combined["subject"] = ""
        if "sender" not in combined.columns:
            combined["sender"] = "unknown@example.com"
        if "attachments" not in combined.columns:
            combined["attachments"] = ""
        if "label" not in combined.columns:
            raise ValueError("Dataset must include a label column.")
        combined = combined.drop_duplicates(subset=["subject", "email_body", "sender"]).reset_index(drop=True)
        combined["label"] = pd.to_numeric(combined["label"], errors="coerce").fillna(0).astype(int)
        combined = self._balance_dataset(combined)
        combined = self._clean_email_frame(combined)
        return combined

    def build_features(self, dataframe: pd.DataFrame) -> FeatureArtifacts:
        frame = dataframe.copy()
        frame["clean_subject"] = frame["subject"].fillna("").map(self.clean_text)
        frame["clean_body"] = frame["email_body"].fillna("").map(self.clean_text)
        frame["combined_text"] = (frame["clean_subject"] + " [SEP] " + frame["clean_body"]).str.strip()
        frame["url_count"] = frame["email_body"].fillna("").str.count(URL_PATTERN)
        frame["urgency_keyword_count"] = frame["combined_text"].map(lambda text: self._keyword_count(text, URGENCY_KEYWORDS))
        frame["financial_term_count"] = frame["combined_text"].map(lambda text: self._keyword_count(text, FINANCIAL_TERMS))
        frame["impersonation_signal_count"] = frame["combined_text"].map(lambda text: self._keyword_count(text, IMPERSONATION_TERMS))
        frame["sender_domain"] = frame["sender"].astype(str).map(self._extract_domain)
        frame["sender_domain_entropy"] = frame["sender_domain"].map(self._domain_entropy)
        frame["link_mismatch_score"] = frame.apply(self._link_mismatch_score, axis=1)
        frame["attachment_presence"] = frame["attachments"].astype(str).str.len().gt(0).astype(int)
        frame["body_length"] = frame["clean_body"].str.len().astype(float)
        frame["exclamation_ratio"] = frame["email_body"].fillna("").map(lambda text: text.count("!") / max(len(text), 1))
        feature_columns = [
            "combined_text",
            "urgency_keyword_count",
            "financial_term_count",
            "impersonation_signal_count",
            "sender_domain_entropy",
            "link_mismatch_score",
            "attachment_presence",
            "url_count",
            "body_length",
            "exclamation_ratio",
        ]
        return FeatureArtifacts(dataframe=frame, metadata_columns=["subject", "sender", "label"], feature_columns=feature_columns)

    def clean_text(self, text: str) -> str:
        if not isinstance(text, str):
            text = ""
        text = html.unescape(text)
        text = HTML_TAG_PATTERN.sub(" ", text)
        text = SIGNATURE_PATTERN.sub(" ", text)
        text = REPLY_CHAIN_PATTERN.sub(" ", text)
        text = URL_PATTERN.sub(" [URL] ", text)
        text = re.sub(r"\s+", " ", text).strip().lower()
        return text

    def _clean_email_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        frame["urls"] = frame["email_body"].fillna("").map(lambda text: URL_PATTERN.findall(text))
        frame["email_body"] = frame["email_body"].fillna("").map(self.clean_text)
        frame["subject"] = frame["subject"].fillna("").map(self.clean_text)
        return frame

    def _balance_dataset(self, frame: pd.DataFrame) -> pd.DataFrame:
        phishing = frame[frame["label"] == 1].copy()
        legitimate = frame[frame["label"] == 0].copy()
        if phishing.empty or legitimate.empty:
            augmented = pd.concat([frame, self._augment_phishing_samples(frame)], ignore_index=True)
            return augmented.sample(frac=1.0, random_state=42).reset_index(drop=True)
        target = min(max(len(phishing), len(legitimate)), max(len(phishing), len(legitimate)))
        legitimate_sample = legitimate.sample(n=min(len(legitimate), target), random_state=42, replace=len(legitimate) < target)
        phishing_sample = phishing.sample(n=min(len(phishing), target), random_state=42, replace=len(phishing) < target)
        augmented = pd.concat([legitimate_sample, phishing_sample, self._augment_phishing_samples(phishing_sample)], ignore_index=True)
        return augmented.sample(frac=1.0, random_state=42).reset_index(drop=True)

    def _augment_phishing_samples(self, phishing_frame: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for row in phishing_frame.head(min(250, len(phishing_frame))).itertuples(index=False):
            subject = f"urgent action required: {getattr(row, 'subject', 'account verification')}"
            body = (
                f"Security notice. Verify your bank account immediately to avoid suspension. "
                f"Reference: {getattr(row, 'email_body', '')[:220]}"
            )
            rows.append({
                "subject": subject,
                "email_body": body,
                "sender": "security-notice@alerts-bank.example",
                "attachments": "statement.pdf",
                "label": 1,
            })
        return pd.DataFrame(rows)

    def _keyword_count(self, text: str, vocabulary: set[str]) -> int:
        lowered = str(text).lower()
        return sum(lowered.count(term) for term in vocabulary)

    def _extract_domain(self, sender: str) -> str:
        sender = str(sender).lower()
        if "@" in sender:
            return sender.split("@", 1)[1]
        return "unknown.local"

    def _domain_entropy(self, domain: str) -> float:
        chars = list(str(domain))
        if not chars:
            return 0.0
        probabilities = pd.Series(chars).value_counts(normalize=True)
        return float(-(probabilities * np.log2(probabilities + 1e-12)).sum())

    def _link_mismatch_score(self, row: pd.Series) -> float:
        sender_domain = row.get("sender_domain", "unknown.local")
        urls = row.get("urls", []) or []
        mismatches = 0
        for url in urls:
            try:
                host = urlparse(url if url.startswith("http") else f"https://{url}").netloc.lower()
                if host and sender_domain not in host:
                    mismatches += 1
            except Exception:
                mismatches += 1
        return float(mismatches)

    def _build_mock_dataset(self) -> pd.DataFrame:
        rows = [
            {"subject": "team lunch tomorrow", "email_body": "please confirm your availability for lunch tomorrow.", "sender": "hr@enron.example", "attachments": "", "label": 0},
            {"subject": "quarterly invoice payment", "email_body": "urgent action required. review the attached invoice and wire funds immediately.", "sender": "cfo-office@pay-portal.example", "attachments": "invoice.pdf", "label": 1},
            {"subject": "vpn maintenance notice", "email_body": "the vpn service will restart tonight. no action required.", "sender": "it-support@enron.example", "attachments": "", "label": 0},
            {"subject": "security verification", "email_body": "verify your bank credentials immediately at https://secure-banking-check.example/login to avoid suspension.", "sender": "security@bank-alerts.example", "attachments": "", "label": 1},
            {"subject": "updated project plan", "email_body": "attached is the updated project plan for next week.", "sender": "manager@enron.example", "attachments": "plan.docx", "label": 0},
            {"subject": "benefits enrollment reminder", "email_body": "please complete your benefits enrollment by friday.", "sender": "benefits@enron.example", "attachments": "", "label": 0},
            {"subject": "wire transfer request", "email_body": "urgent. send wire payment before end of day and confirm once complete.", "sender": "finance-ops@vendor-payments.example", "attachments": "payment-details.xlsx", "label": 1},
            {"subject": "mailbox storage warning", "email_body": "your mailbox will be disabled unless you verify credentials now at www.verify-mail-access.example.", "sender": "mail-admin@alerts.example", "attachments": "", "label": 1},
            {"subject": "office move update", "email_body": "the office move schedule is attached for facilities planning.", "sender": "facilities@enron.example", "attachments": "schedule.pdf", "label": 0},
            {"subject": "quarterly security awareness", "email_body": "please attend the quarterly security awareness training session.", "sender": "security-awareness@enron.example", "attachments": "", "label": 0},
            {"subject": "account suspension notice", "email_body": "action required immediately. your payroll account will be suspended unless you reset your password.", "sender": "payroll-security@alerts-payroll.example", "attachments": "", "label": 1},
            {"subject": "executive request", "email_body": "this is the ceo. purchase gift cards and send the codes right away.", "sender": "ceo-office@exec-mail.example", "attachments": "", "label": 1},
        ]
        return pd.DataFrame(rows)
