"""Synchronous HTTP client for the AMBIE API."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import httpx

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

DEFAULT_BASE_URL = "https://ambie.ai"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3
RETRY_STATUS = {429, 500, 502, 503, 504}
SDK_VERSION = "0.1.0"


class AmbieError(Exception):
    """Raised on non-2xx responses after retries."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(f"[{status} {code}] {message}")
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id


AudioInput = Union[str, Path, bytes, BinaryIO]


class Client:
    """Synchronous client for the AMBIE API.

    Example:
        >>> from ambie import Client
        >>> with Client(api_key="amb_live_...") as c:
        ...     r = c.transcribe(audio="meeting.mp3", diarize=True, summarize=True)
        ...     print(r.text, r.summary)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: str = f"ambie-python/{SDK_VERSION}",
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self._http = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        params: Optional[dict] = None,
        accept: str = "application/json",
        raw: bool = False,
    ) -> Any:
        url = self.base_url + path
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": self.user_agent,
            "Accept": accept,
        }
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                r = self._http.request(
                    method,
                    url,
                    json=json,
                    data=data,
                    files=files,
                    params=params,
                    headers=headers,
                )
            except httpx.RequestError as e:
                last_exc = e
                if attempt >= self.max_retries:
                    raise
                time.sleep(0.25 * (2**attempt))
                continue

            if r.is_success:
                if raw or accept != "application/json":
                    return r.text
                if not r.content:
                    return None
                return r.json()

            if r.status_code in RETRY_STATUS and attempt < self.max_retries:
                try:
                    retry_after = float(r.headers.get("retry-after", "0"))
                except ValueError:
                    retry_after = 0
                delay = retry_after if retry_after > 0 else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            code = "http_error"
            message = f"HTTP {r.status_code}"
            try:
                j = r.json()
                message = j.get("error") or j.get("message") or message
                code = j.get("code", code)
            except ValueError:
                pass
            raise AmbieError(
                r.status_code, code, message, r.headers.get("x-request-id")
            )
        if last_exc:
            raise last_exc
        raise RuntimeError("unreachable")

    # --- Transcription ---------------------------------------------------

    def transcribe(
        self,
        audio: Optional[AudioInput] = None,
        *,
        url: Optional[str] = None,
        engine: str = "deepgram",
        language: Optional[str] = None,
        format: str = "json",
        translate: bool = False,
        callback_url: Optional[str] = None,
        client_id: Optional[str] = None,
        diarize: bool = False,
        summarize: bool = False,
        key_phrases: bool = False,
        action_items: bool = False,
        chapters: bool = False,
        **extra: Any,
    ) -> Union[TranscriptionResult, AsyncAccepted, str]:
        """Transcribe an audio file or remote URL.

        Pass ``audio=`` (path/bytes/file-object) OR ``url=`` (remote URL).
        Returns ``TranscriptionResult`` synchronously, or ``AsyncAccepted`` if
        ``callback_url`` is set, or raw text/SRT/VTT if ``format`` is non-json.
        """
        if audio is None and url is None:
            raise ValueError("transcribe requires either `audio` or `url`")

        files = None
        if audio is not None:
            if isinstance(audio, (str, Path)):
                p = Path(audio)
                files = {"audio": (p.name, p.open("rb"), "application/octet-stream")}
            elif isinstance(audio, (bytes, bytearray)):
                files = {
                    "audio": ("audio.bin", bytes(audio), "application/octet-stream")
                }
            else:
                files = {"audio": ("audio.bin", audio, "application/octet-stream")}

        form: Dict[str, Any] = {"engine": engine, "format": format}
        if url is not None:
            form["url"] = url
        if language is not None:
            form["language"] = language
        if callback_url is not None:
            form["callback_url"] = callback_url
        if client_id is not None:
            form["client_id"] = client_id
        for flag_name, flag_val in (
            ("translate", translate),
            ("diarize", diarize),
            ("summarize", summarize),
            ("key_phrases", key_phrases),
            ("action_items", action_items),
            ("chapters", chapters),
        ):
            form[flag_name] = "true" if flag_val else "false"
        for k, v in extra.items():
            if isinstance(v, bool):
                form[k] = "true" if v else "false"
            elif v is not None:
                form[k] = str(v)

        accept_map = {
            "json": "application/json",
            "text": "text/plain",
            "srt": "application/x-subrip",
            "vtt": "text/vtt",
        }
        resp = self._request(
            "POST",
            "/api/v1/transcribe",
            data=form,
            files=files,
            accept=accept_map.get(format, "application/json"),
        )
        if format != "json":
            return resp  # type: ignore[return-value]
        if isinstance(resp, dict):
            if resp.get("status") in ("queued", "processing"):
                return AsyncAccepted.from_dict(resp)
            return TranscriptionResult.from_dict(resp)
        return resp  # type: ignore[return-value]

    def get_transcribe_job(self, request_id: str) -> JobStatus:
        d = self._request("GET", f"/api/v1/transcribe/{request_id}")
        return JobStatus(**{k: d.get(k) for k in JobStatus.__dataclass_fields__})

    # --- Translation -----------------------------------------------------

    def translate(
        self,
        text: str,
        target_lang: str,
        *,
        source_lang: Optional[str] = None,
        formality: Optional[str] = None,
        context: Optional[str] = None,
        callback_url: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Union[TranslationResult, AsyncAccepted]:
        body = {"text": text, "target_lang": target_lang}
        for k, v in {
            "source_lang": source_lang,
            "formality": formality,
            "context": context,
            "callback_url": callback_url,
            "client_id": client_id,
        }.items():
            if v is not None:
                body[k] = v
        d = self._request("POST", "/api/v1/translate", json=body)
        if d.get("status") in ("queued", "processing"):
            return AsyncAccepted.from_dict(d)
        return TranslationResult(
            **{k: d.get(k) for k in TranslationResult.__dataclass_fields__ if k in d}
        )

    def get_translate_job(self, request_id: str) -> JobStatus:
        d = self._request("GET", f"/api/v1/translate/{request_id}")
        return JobStatus(**{k: d.get(k) for k in JobStatus.__dataclass_fields__})

    # --- TTS -------------------------------------------------------------

    def tts(self, text: str, **opts: Any) -> Union[TtsResult, AsyncAccepted]:
        body = {"text": text, **{k: v for k, v in opts.items() if v is not None}}
        d = self._request("POST", "/api/v1/tts", json=body)
        if d.get("status") in ("queued", "processing"):
            return AsyncAccepted.from_dict(d)
        return TtsResult(
            **{k: d.get(k) for k in TtsResult.__dataclass_fields__ if k in d}
        )

    def get_tts_job(self, request_id: str) -> JobStatus:
        d = self._request("GET", f"/api/v1/tts/{request_id}")
        return JobStatus(**{k: d.get(k) for k in JobStatus.__dataclass_fields__})

    # --- Sentiment -------------------------------------------------------

    def sentiment(
        self,
        text: Union[str, List[str]],
        *,
        callback_url: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Union[SentimentResult, AsyncAccepted]:
        body: Dict[str, Any] = {"text": text}
        if callback_url:
            body["callback_url"] = callback_url
        if client_id:
            body["client_id"] = client_id
        d = self._request("POST", "/api/v1/sentiment", json=body)
        if d.get("status") in ("queued", "processing"):
            return AsyncAccepted.from_dict(d)
        return SentimentResult(
            **{k: d.get(k) for k in SentimentResult.__dataclass_fields__ if k in d}
        )

    def get_sentiment_job(self, request_id: str) -> JobStatus:
        d = self._request("GET", f"/api/v1/sentiment/{request_id}")
        return JobStatus(**{k: d.get(k) for k in JobStatus.__dataclass_fields__})

    # --- Summarize -------------------------------------------------------

    def summarize(
        self,
        *,
        text: Optional[str] = None,
        url: Optional[str] = None,
        max_length: Optional[int] = None,
        callback_url: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Union[SummarizeResult, AsyncAccepted]:
        if text is None and url is None:
            raise ValueError("summarize requires either `text` or `url`")
        body: Dict[str, Any] = {}
        for k, v in {
            "text": text,
            "url": url,
            "max_length": max_length,
            "callback_url": callback_url,
            "client_id": client_id,
        }.items():
            if v is not None:
                body[k] = v
        d = self._request("POST", "/api/v1/summarize", json=body)
        if d.get("status") in ("queued", "processing"):
            return AsyncAccepted.from_dict(d)
        return SummarizeResult(
            **{k: d.get(k) for k in SummarizeResult.__dataclass_fields__ if k in d}
        )

    def get_summarize_job(self, request_id: str) -> JobStatus:
        d = self._request("GET", f"/api/v1/summarize/{request_id}")
        return JobStatus(**{k: d.get(k) for k in JobStatus.__dataclass_fields__})

    # --- Embeddings ------------------------------------------------------

    def embeddings(
        self,
        text: Union[str, List[str]],
        *,
        model: Optional[str] = None,
        callback_url: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Union[EmbeddingsResult, AsyncAccepted]:
        body: Dict[str, Any] = {"text": text}
        for k, v in {
            "model": model,
            "callback_url": callback_url,
            "client_id": client_id,
        }.items():
            if v is not None:
                body[k] = v
        d = self._request("POST", "/api/v1/embeddings", json=body)
        if d.get("status") in ("queued", "processing"):
            return AsyncAccepted.from_dict(d)
        return EmbeddingsResult(
            **{k: d.get(k) for k in EmbeddingsResult.__dataclass_fields__ if k in d}
        )

    def get_embeddings_job(self, request_id: str) -> JobStatus:
        d = self._request("GET", f"/api/v1/embeddings/{request_id}")
        return JobStatus(**{k: d.get(k) for k in JobStatus.__dataclass_fields__})

    # --- Rerank ----------------------------------------------------------

    def rerank(
        self,
        query: str,
        documents: List[str],
        *,
        top_k: Optional[int] = None,
        callback_url: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Union[RerankResult, AsyncAccepted]:
        body: Dict[str, Any] = {"query": query, "documents": documents}
        for k, v in {
            "top_k": top_k,
            "callback_url": callback_url,
            "client_id": client_id,
        }.items():
            if v is not None:
                body[k] = v
        d = self._request("POST", "/api/v1/rerank", json=body)
        if d.get("status") in ("queued", "processing"):
            return AsyncAccepted.from_dict(d)
        return RerankResult(
            **{k: d.get(k) for k in RerankResult.__dataclass_fields__ if k in d}
        )

    def get_rerank_job(self, request_id: str) -> JobStatus:
        d = self._request("GET", f"/api/v1/rerank/{request_id}")
        return JobStatus(**{k: d.get(k) for k in JobStatus.__dataclass_fields__})

    # --- Moderate --------------------------------------------------------

    def moderate(
        self,
        text: str,
        *,
        callback_url: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Union[ModerateResult, AsyncAccepted]:
        body: Dict[str, Any] = {"text": text}
        if callback_url:
            body["callback_url"] = callback_url
        if client_id:
            body["client_id"] = client_id
        d = self._request("POST", "/api/v1/moderate", json=body)
        if d.get("status") in ("queued", "processing"):
            return AsyncAccepted.from_dict(d)
        return ModerateResult(
            **{k: d.get(k) for k in ModerateResult.__dataclass_fields__ if k in d}
        )

    def get_moderate_job(self, request_id: str) -> JobStatus:
        d = self._request("GET", f"/api/v1/moderate/{request_id}")
        return JobStatus(**{k: d.get(k) for k in JobStatus.__dataclass_fields__})

    # --- Detect language -------------------------------------------------

    def detect_language(
        self,
        text: str,
        *,
        callback_url: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Union[DetectLangResult, AsyncAccepted]:
        body: Dict[str, Any] = {"text": text}
        if callback_url:
            body["callback_url"] = callback_url
        if client_id:
            body["client_id"] = client_id
        d = self._request("POST", "/api/v1/detect-lang", json=body)
        if d.get("status") in ("queued", "processing"):
            return AsyncAccepted.from_dict(d)
        return DetectLangResult(
            **{k: d.get(k) for k in DetectLangResult.__dataclass_fields__ if k in d}
        )
