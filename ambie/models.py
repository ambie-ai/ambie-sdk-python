"""AMBIE response/request models. Lean dataclasses — long-tail metadata
remains accessible via dict-like access on the raw response.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AsyncAccepted:
    request_id: str
    poll_url: str
    status: str
    client_id: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AsyncAccepted":
        return cls(
            request_id=d["request_id"],
            poll_url=d["poll_url"],
            status=d["status"],
            client_id=d.get("client_id"),
            created_at=d.get("created_at"),
        )


@dataclass
class JobStatus:
    request_id: str
    status: str
    client_id: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class TranscriptionResult:
    request_id: str
    engine: str
    duration: float
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    summary: Optional[str] = None
    diarized_text: Optional[str] = None
    speaker_count: Optional[int] = None
    key_phrases: Optional[List[str]] = None
    paragraphs: Optional[List[str]] = None
    words: Optional[List[Dict[str, Any]]] = None
    utterances: Optional[List[Dict[str, Any]]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    chapters: Optional[List[Dict[str, Any]]] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TranscriptionResult":
        known = {
            "request_id",
            "engine",
            "duration",
            "text",
            "language",
            "confidence",
            "summary",
            "diarized_text",
            "speaker_count",
            "key_phrases",
            "paragraphs",
            "words",
            "utterances",
            "action_items",
            "chapters",
        }
        return cls(**{k: v for k, v in d.items() if k in known}, raw=d)


@dataclass
class TranslationResult:
    request_id: str
    source_lang: str
    target_lang: str
    source_text: str
    translated_text: str
    confidence: Optional[float] = None
    client_id: Optional[str] = None


@dataclass
class TtsResult:
    request_id: str
    audio_url: str
    voice: str
    encoding: str
    duration: Optional[float] = None
    client_id: Optional[str] = None


@dataclass
class SentimentResult:
    request_id: str
    results: List[Dict[str, Any]]
    client_id: Optional[str] = None


@dataclass
class SummarizeResult:
    request_id: str
    summary: str
    source_length: Optional[int] = None
    summary_length: Optional[int] = None
    client_id: Optional[str] = None


@dataclass
class EmbeddingsResult:
    request_id: str
    model: str
    dimensions: int
    embeddings: List[List[float]]
    client_id: Optional[str] = None


@dataclass
class RerankResult:
    request_id: str
    results: List[Dict[str, Any]]
    client_id: Optional[str] = None


@dataclass
class ModerateResult:
    request_id: str
    flagged: bool
    categories: Dict[str, bool]
    scores: Optional[Dict[str, float]] = None
    client_id: Optional[str] = None


@dataclass
class DetectLangResult:
    request_id: str
    language: str
    confidence: float
    alternatives: Optional[List[Dict[str, Any]]] = None
    client_id: Optional[str] = None
