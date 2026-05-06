# Changelog

All notable changes to this SDK are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [0.1.0] - 2026-05-06

Initial public release.

- Typed clients for transcribe, translate, TTS, sentiment, summarize, embeddings, rerank, moderate, and detect-language.
- Bearer-token auth with exponential-backoff retry on 429 and 5xx responses (honors `Retry-After`).
- Sync and async (callback-based) modes for every endpoint.
- Webhook signature verification helper for the Stripe-compatible `X-Ambie-Signature` header.
- File uploads via path, file-like object, or bytes for transcription.
- MIT licensed.
