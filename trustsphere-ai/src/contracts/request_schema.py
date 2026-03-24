"""Versioned API request schemas for TrustSphere serving endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .incident_schema import INCIDENT_SCHEMA_VERSION
from .log_schema import NormalizedLog

EMAIL_REQUEST_SCHEMA_VERSION = "api.email.v1"
URL_REQUEST_SCHEMA_VERSION = "api.url.v1"
CREDENTIAL_REQUEST_SCHEMA_VERSION = "api.credential.v1"
ATTACHMENT_REQUEST_SCHEMA_VERSION = "api.attachment.v1"
PROMPT_GUARD_REQUEST_SCHEMA_VERSION = "api.prompt_guard.v1"


class EmailDetectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[EMAIL_REQUEST_SCHEMA_VERSION] = EMAIL_REQUEST_SCHEMA_VERSION
    email_text: str = Field(default="")
    subject: str = Field(default="")
    body: str = Field(default="")
    sender: str = Field(default="unknown@example.com")
    attachments: str = Field(default="")


class URLDetectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[URL_REQUEST_SCHEMA_VERSION] = URL_REQUEST_SCHEMA_VERSION
    url: str


class CredentialDetectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[CREDENTIAL_REQUEST_SCHEMA_VERSION] = CREDENTIAL_REQUEST_SCHEMA_VERSION
    text: str
    commit_message: str = Field(default="")
    paste_context: str = Field(default="")


class AttachmentDetectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[ATTACHMENT_REQUEST_SCHEMA_VERSION] = ATTACHMENT_REQUEST_SCHEMA_VERSION
    filename: str
    size_bytes: int
    content_text: str = Field(default="")
    event_context: str = Field(default="")
    post_download_action: str = Field(default="")


class PromptGuardRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[PROMPT_GUARD_REQUEST_SCHEMA_VERSION] = PROMPT_GUARD_REQUEST_SCHEMA_VERSION
    prompt: str


class IncidentAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[INCIDENT_SCHEMA_VERSION] = INCIDENT_SCHEMA_VERSION
    logs: list[NormalizedLog] = Field(default_factory=list)
