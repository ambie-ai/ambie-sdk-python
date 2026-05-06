"""Official Python SDK for AMBIE.

https://ambie.ai/sdk
"""

from .client import AmbieError, Client
from .models import (
    AsyncAccepted,
    DetectLangResult,
    EmbeddingsResult,
    JobStatus,
    ModerateResult,
    RerankResult,
    SentimentResult,
    SummarizeResult,
    TranscriptionResult,
    TranslationResult,
    TtsResult,
)
from .webhook import WebhookVerificationError, verify_webhook_signature

__version__ = "0.1.0"
__all__ = [
    "AmbieError",
    "Client",
    "AsyncAccepted",
    "DetectLangResult",
    "EmbeddingsResult",
    "JobStatus",
    "ModerateResult",
    "RerankResult",
    "SentimentResult",
    "SummarizeResult",
    "TranscriptionResult",
    "TranslationResult",
    "TtsResult",
    "WebhookVerificationError",
    "verify_webhook_signature",
]
