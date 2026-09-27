"""Source provenance for content that tools retrieve from external services."""

import hashlib
from datetime import datetime, timezone
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    field_validator,
    model_validator,
)

Sha256Digest = Annotated[
    str,
    BeforeValidator(lambda value: value.lower() if isinstance(value, str) else value),
    StringConstraints(pattern=r"^[0-9a-f]{64}$"),
]


class SourceProvenance(BaseModel):
    """Where, when, and how a tool retrieved external content, and which exact bytes came back.

    One instance describes one request. The typed fields answer the reproducibility questions
    every retrieval shares: which provider, which record, which version, when, and whether the
    response bytes are known exactly (``content_sha256`` and ``size_bytes``). Anything specific
    to one kind of source (genomic coordinates, an assembly, a licence, an access classification)
    goes in ``details`` as reported by that source.

    Every field must be credential-free. Tools are responsible for this: build
    ``request_parameters`` from the options that change the response, never from the raw HTTP
    parameters or headers that carry an API key. ``source_url`` is checked only for embedded
    userinfo.
    """

    provider: str = Field(title="Provider", description="External service or repository that supplied the content")
    source_url: str | None = Field(
        default=None,
        title="Source URL",
        description="HTTP URL for the retrieved record or request",
    )
    identifier: str | None = Field(
        default=None,
        title="Identifier",
        description="Stable provider identifier, such as an accession, DOI, PMID, or part ID",
    )
    version: str | None = Field(
        default=None,
        title="Version",
        description="Provider record version or release identifier when one exists",
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        title="Retrieved At",
        description="Timezone-aware timestamp recording when the content was retrieved",
    )
    media_type: str | None = Field(
        default=None,
        title="Media Type",
        description="Media type of the retrieved representation, such as text/x-fasta",
    )
    content_sha256: Sha256Digest | None = Field(
        default=None,
        title="Content SHA-256",
        description="Lowercase SHA-256 digest of the exact response bytes, when they were kept",
    )
    size_bytes: int | None = Field(
        default=None,
        ge=0,
        title="Size Bytes",
        description="Length of the exact response bytes; set together with content_sha256",
    )
    request_parameters: dict[str, JsonValue] = Field(
        default_factory=dict,
        title="Request Parameters",
        description="Request options that change the returned bytes, needed to reproduce the request",
    )
    details: dict[str, JsonValue] = Field(
        default_factory=dict,
        title="Details",
        description="Provider-specific context, such as assembly, coordinates, or licence",
    )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    def matches(self, content: bytes) -> bool:
        """Return whether bytes match the recorded size and digest; False when none was recorded."""
        return (
            self.content_sha256 is not None
            and len(content) == self.size_bytes
            and hashlib.sha256(content).hexdigest() == self.content_sha256
        )

    @field_validator("provider")
    @classmethod
    def _provider_must_not_be_blank(cls, value: str) -> str:
        provider = value.strip()
        if not provider:
            raise ValueError("provider must not be blank")
        return provider

    @field_validator("retrieved_at")
    @classmethod
    def _retrieved_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        return value

    @field_validator("source_url")
    @classmethod
    def _source_url_must_be_safe_http(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be an absolute HTTP or HTTPS URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("source_url must not contain credentials")
        return value

    @model_validator(mode="after")
    def _digest_and_size_together(self) -> "SourceProvenance":
        if (self.content_sha256 is None) != (self.size_bytes is None):
            raise ValueError("content_sha256 and size_bytes must be set together")
        return self
