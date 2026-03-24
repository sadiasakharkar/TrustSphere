"""Feature engineering for URL phishing detection."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import ipaddress
import json
import logging
import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
COMMON_BRANDS = [
    "google", "microsoft", "apple", "amazon", "paypal", "netflix", "facebook",
    "instagram", "whatsapp", "bankofamerica", "barclays", "hsbc", "adobe", "dropbox",
]
SHORTENER_DOMAINS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "rb.gy"}
SUSPICIOUS_TLDS = {"top", "xyz", "click", "gq", "tk", "ml", "work", "buzz"}
SUSPICIOUS_KEYWORDS = {"login", "verify", "secure", "update", "confirm", "account", "bank", "pay", "invoice", "gift"}
SPECIAL_CHARS = "@-_=%?&~"


@dataclass(slots=True)
class URLFeatureArtifacts:
    dataframe: pd.DataFrame
    feature_columns: list[str]


class URLPhishingFeatureEngineer:
    """Build engineered lexical, host, and semantic URL features."""

    def build_dataset(self, dataframes: list[pd.DataFrame | dict[str, Any]] | None = None) -> pd.DataFrame:
        if dataframes:
            normalized_frames = [item if isinstance(item, pd.DataFrame) else pd.DataFrame([item]) for item in dataframes]
            frame = pd.concat(normalized_frames, ignore_index=True)
        else:
            frame = self._mock_dataset()
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        if "url" not in frame.columns:
            raise ValueError("URL dataset requires a url column.")
        if "label" not in frame.columns:
            raise ValueError("URL dataset requires a label column.")
        frame = frame.drop_duplicates(subset=["url"]).reset_index(drop=True)
        frame["label"] = pd.to_numeric(frame["label"], errors="coerce").fillna(0).astype(int)
        frame["commit_context"] = frame.get("commit_context", "")
        frame["domain_age_days"] = pd.to_numeric(frame.get("domain_age_days", np.nan), errors="coerce")
        frame["ssl_present"] = pd.to_numeric(frame.get("ssl_present", np.nan), errors="coerce")
        frame["whois_private"] = pd.to_numeric(frame.get("whois_private", np.nan), errors="coerce")
        return frame

    def build_features(self, frame: pd.DataFrame) -> URLFeatureArtifacts:
        dataset = frame.copy()
        parsed = dataset["url"].astype(str).map(urlparse)
        dataset["scheme"] = parsed.map(lambda p: p.scheme.lower())
        dataset["netloc"] = parsed.map(lambda p: p.netloc.lower())
        dataset["path"] = parsed.map(lambda p: p.path)
        dataset["query"] = parsed.map(lambda p: p.query)
        dataset["hostname"] = parsed.map(lambda p: (p.hostname or "").lower())
        dataset["tld"] = dataset["hostname"].map(self._extract_tld)
        dataset["registered_domain"] = dataset["hostname"].map(self._registered_domain)
        dataset["subdomain"] = dataset.apply(lambda row: self._subdomain(row["hostname"], row["registered_domain"]), axis=1)

        feature_map = {
            "url_length": dataset["url"].str.len(),
            "hostname_length": dataset["hostname"].str.len(),
            "path_length": dataset["path"].str.len(),
            "query_length": dataset["query"].str.len(),
            "digit_count": dataset["url"].str.count(r"\d"),
            "digit_ratio": dataset["url"].map(lambda value: self._ratio(re.findall(r"\d", str(value)), str(value))),
            "dot_count": dataset["url"].str.count(r"\."),
            "hyphen_count": dataset["url"].str.count(r"-"),
            "underscore_count": dataset["url"].str.count(r"_"),
            "slash_count": dataset["url"].str.count(r"/"),
            "question_count": dataset["url"].str.count(r"\?"),
            "equals_count": dataset["url"].str.count(r"="),
            "ampersand_count": dataset["url"].str.count(r"&"),
            "percent_count": dataset["url"].str.count(r"%"),
            "at_count": dataset["url"].str.count(r"@"),
            "tilde_count": dataset["url"].str.count(r"~"),
            "special_char_count": dataset["url"].map(lambda value: sum(str(value).count(ch) for ch in SPECIAL_CHARS)),
            "special_char_ratio": dataset["url"].map(lambda value: self._special_ratio(str(value))),
            "subdomain_count": dataset["subdomain"].map(lambda value: 0 if not value else value.count(".") + 1),
            "path_segment_count": dataset["path"].map(lambda value: len([segment for segment in str(value).split("/") if segment])),
            "query_param_count": dataset["query"].map(lambda value: len(parse_qs(str(value)))),
            "fragment_present": dataset["url"].str.contains("#", regex=False).astype(int),
            "http_scheme": (dataset["scheme"] == "http").astype(int),
            "https_scheme": (dataset["scheme"] == "https").astype(int),
            "ip_in_host": dataset["hostname"].map(self._is_ip_address).astype(int),
            "contains_port": dataset["netloc"].str.contains(r":\d+$", regex=True).astype(int),
            "punycode_flag": dataset["hostname"].str.contains("xn--", regex=False).astype(int),
            "shortener_flag": dataset["registered_domain"].isin(SHORTENER_DOMAINS).astype(int),
            "suspicious_tld_flag": dataset["tld"].isin(SUSPICIOUS_TLDS).astype(int),
            "brand_similarity_max": dataset["hostname"].map(self._brand_similarity),
            "brand_keyword_count": dataset["hostname"].map(lambda value: sum(brand in str(value) for brand in COMMON_BRANDS)),
            "suspicious_keyword_count": dataset["url"].str.lower().map(lambda value: sum(value.count(keyword) for keyword in SUSPICIOUS_KEYWORDS)),
            "repeated_char_score": dataset["url"].map(self._repeated_char_score),
            "host_entropy": dataset["hostname"].map(self._entropy),
            "path_entropy": dataset["path"].map(self._entropy),
            "query_entropy": dataset["query"].map(self._entropy),
            "url_entropy": dataset["url"].map(self._entropy),
            "vowel_ratio_host": dataset["hostname"].map(self._vowel_ratio),
            "consonant_ratio_host": dataset["hostname"].map(self._consonant_ratio),
            "alpha_ratio_host": dataset["hostname"].map(lambda value: self._alpha_ratio(str(value))),
            "numeric_token_count": dataset["hostname"].map(lambda value: len(re.findall(r"\d+", str(value)))),
            "long_token_count": dataset["hostname"].map(lambda value: len([token for token in re.split(r"[.-]", str(value)) if len(token) >= 12])),
            "uppercase_ratio": dataset["url"].map(lambda value: self._ratio(re.findall(r"[A-Z]", str(value)), str(value))),
            "hostname_token_count": dataset["hostname"].map(lambda value: len([token for token in re.split(r"[.-]", str(value)) if token])),
            "path_token_count": dataset["path"].map(lambda value: len([token for token in re.split(r"[/_-]", str(value)) if token])),
            "query_token_count": dataset["query"].map(lambda value: len([token for token in re.split(r"[=&]", str(value)) if token])),
            "double_slash_path": dataset["url"].str.contains(r"https?://.*/.*//", regex=True).astype(int),
            "login_like_path": dataset["path"].str.lower().str.contains("login|signin|verify|secure", regex=True).astype(int),
            "file_extension_risk": dataset["path"].str.lower().str.contains(r"\.(?:exe|zip|scr|js|jar|html?)$", regex=True).astype(int),
            "redirect_hint": dataset["query"].str.lower().str.contains("redirect|url=|next=|continue=", regex=True).astype(int),
            "ssl_present_feature": dataset["ssl_present"].fillna((dataset["scheme"] == "https").astype(int)),
            "whois_private_feature": dataset["whois_private"].fillna(0),
            "domain_age_days_feature": dataset["domain_age_days"].fillna(dataset["registered_domain"].map(lambda value: 3650 if value in {"google.com", "amazon.com", "paypal.com"} else 30)),
            "young_domain_flag": dataset["domain_age_days"].fillna(30).lt(90).astype(int),
            "alexa_like_flag": dataset["registered_domain"].isin({"google.com", "youtube.com", "amazon.com", "facebook.com", "wikipedia.org"}).astype(int),
            "whois_missing_flag": dataset["domain_age_days"].isna().astype(int),
            "brand_subdomain_mismatch": dataset.apply(lambda row: self._brand_subdomain_mismatch(row["hostname"], row["registered_domain"]), axis=1),
            "safe_word_count": dataset["url"].str.lower().map(lambda value: sum(value.count(word) for word in {"about", "support", "help", "docs", "status"})),
            "phishy_prefix_flag": dataset["hostname"].str.lower().str.startswith(("secure-", "verify-", "login-")).astype(int),
            "unicode_like_flag": dataset["url"].map(lambda value: int(any(ord(ch) > 127 for ch in str(value)))),
            "trigram_weirdness": dataset["hostname"].map(self._trigram_weirdness),
        }
        for name, values in feature_map.items():
            dataset[name] = pd.to_numeric(values, errors="coerce").fillna(0.0)
        feature_columns = list(feature_map.keys())
        self._save_schema(feature_columns)
        return URLFeatureArtifacts(dataframe=dataset, feature_columns=feature_columns)

    def _extract_tld(self, hostname: str) -> str:
        parts = [part for part in str(hostname).split(".") if part]
        return parts[-1] if parts else ""

    def _registered_domain(self, hostname: str) -> str:
        parts = [part for part in str(hostname).split(".") if part]
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return str(hostname)

    def _subdomain(self, hostname: str, registered_domain: str) -> str:
        if not hostname or not registered_domain or hostname == registered_domain:
            return ""
        suffix = f".{registered_domain}"
        return hostname[:-len(suffix)] if hostname.endswith(suffix) else ""

    def _brand_similarity(self, hostname: str) -> float:
        hostname = str(hostname)
        if not hostname:
            return 0.0
        return max(SequenceMatcher(None, hostname, brand).ratio() for brand in COMMON_BRANDS)

    def _entropy(self, text: str) -> float:
        chars = list(str(text))
        if not chars:
            return 0.0
        probabilities = pd.Series(chars).value_counts(normalize=True)
        return float(-(probabilities * np.log2(probabilities + 1e-12)).sum())

    def _ratio(self, subset: list[str], text: str) -> float:
        text = str(text)
        return float(len(subset) / max(len(text), 1))

    def _special_ratio(self, text: str) -> float:
        return sum(text.count(ch) for ch in SPECIAL_CHARS) / max(len(text), 1)

    def _is_ip_address(self, hostname: str) -> bool:
        try:
            ipaddress.ip_address(str(hostname))
            return True
        except Exception:
            return False

    def _repeated_char_score(self, text: str) -> float:
        matches = re.findall(r"(.)\1{2,}", str(text))
        return float(len(matches))

    def _vowel_ratio(self, text: str) -> float:
        text = re.sub(r"[^a-z]", "", str(text).lower())
        return sum(ch in "aeiou" for ch in text) / max(len(text), 1)

    def _consonant_ratio(self, text: str) -> float:
        text = re.sub(r"[^a-z]", "", str(text).lower())
        return sum(ch not in "aeiou" for ch in text) / max(len(text), 1)

    def _alpha_ratio(self, text: str) -> float:
        return len(re.findall(r"[A-Za-z]", text)) / max(len(text), 1)

    def _brand_subdomain_mismatch(self, hostname: str, registered_domain: str) -> int:
        hostname = str(hostname)
        registered_domain = str(registered_domain)
        for brand in COMMON_BRANDS:
            if brand in hostname and brand not in registered_domain:
                return 1
        return 0

    def _trigram_weirdness(self, hostname: str) -> float:
        hostname = re.sub(r"[^a-z]", "", str(hostname).lower())
        if len(hostname) < 3:
            return 0.0
        trigrams = [hostname[index:index + 3] for index in range(len(hostname) - 2)]
        vowel_trigrams = sum(any(ch in "aeiou" for ch in trigram) for trigram in trigrams)
        return 1.0 - (vowel_trigrams / max(len(trigrams), 1))

    def _save_schema(self, feature_columns: list[str]) -> None:
        path = Path("security_ai/artifacts/url_feature_schema_preview.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")

    def _mock_dataset(self) -> pd.DataFrame:
        rows = [
            {"url": "https://accounts.google.com/signin", "label": 0, "domain_age_days": 7000, "ssl_present": 1, "whois_private": 0},
            {"url": "http://secure-google-login.verify-account.xyz/auth/login.php", "label": 1, "domain_age_days": 15, "ssl_present": 0, "whois_private": 1},
            {"url": "https://paypal.com/security/update", "label": 0, "domain_age_days": 6500, "ssl_present": 1, "whois_private": 0},
            {"url": "http://paypal-login-secure.top/verify?redirect=bank", "label": 1, "domain_age_days": 22, "ssl_present": 0, "whois_private": 1},
            {"url": "https://github.com/login", "label": 0, "domain_age_days": 6000, "ssl_present": 1, "whois_private": 0},
            {"url": "http://192.168.0.10/login/verify/index.html", "label": 1, "domain_age_days": 1, "ssl_present": 0, "whois_private": 1},
            {"url": "https://docs.python.org/3/", "label": 0, "domain_age_days": 6500, "ssl_present": 1, "whois_private": 0},
            {"url": "https://bit.ly/3SecureBankingLogin", "label": 1, "domain_age_days": 30, "ssl_present": 1, "whois_private": 1},
            {"url": "https://amazon.com/ap/signin", "label": 0, "domain_age_days": 7500, "ssl_present": 1, "whois_private": 0},
            {"url": "http://amazon-verify-account.click/secure-login?next=invoice", "label": 1, "domain_age_days": 10, "ssl_present": 0, "whois_private": 1},
        ]
        return pd.DataFrame(rows)
