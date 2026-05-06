# ambie

Official Python SDK for [AMBIE](https://ambie.ai).

Speech-to-text in noisy environments, translation, TTS, embeddings, sentiment, summarization, content moderation, and language detection — over a single typed client.

## Install

Install directly from this GitHub repo:

```bash
pip install git+https://github.com/ambie-ai/ambie-sdk-python.git
```

Pin to a tag:

```bash
pip install git+https://github.com/ambie-ai/ambie-sdk-python.git@v0.1.0
```

Requires Python 3.9+.

> The SDK source is open here on GitHub. We're not publishing to PyPI yet — install directly from this repo. Once v1.0.0 ships, we'll mirror to PyPI and the install line will shorten to `pip install ambie`.

## Quickstart

```python
from ambie import Client

with Client(api_key="amb_live_...") as c:
    result = c.transcribe(
        audio="meeting.mp3",
        engine="deepgram",
        diarize=True,
        summarize=True,
    )
    print(result.text)
    print(result.summary)
    print(f"{result.speaker_count} speakers detected")

    # Translate text
    t = c.translate("Hello, world!", target_lang="es")
    print(t.translated_text)

    # Embed text for semantic search
    e = c.embeddings(["alpha", "beta", "gamma"])
    print(e.dimensions, len(e.embeddings))
```

## Async mode

Pass a `callback_url` to get the result delivered to your webhook:

```python
accepted = c.transcribe(
    url="https://cdn.example.com/long-recording.mp3",
    callback_url="https://yourserver.com/webhooks/ambie",
)
print(accepted.request_id, accepted.poll_url)

# Or poll status manually:
status = c.get_transcribe_job(accepted.request_id)
```

## Webhook verification

```python
from ambie import verify_webhook_signature, WebhookVerificationError

# In your webhook handler (e.g. FastAPI/Flask/Django):
signature = request.headers["x-ambie-signature"]
body = request.body  # raw bytes, NOT the parsed JSON

try:
    verify_webhook_signature(
        signature=signature,
        body=body,
        secret=os.environ["AMBIE_WEBHOOK_SECRET"],
    )
except WebhookVerificationError:
    return Response(status_code=401)

# Safe to parse and act on body after this line.
```

## Configuration

| Argument       | Default                  | Description                               |
| -------------- | ------------------------ | ----------------------------------------- |
| `api_key`      | **required**             | API key from [/signup](https://ambie.ai/signup) |
| `base_url`     | `https://ambie.ai`       | Override for staging                      |
| `timeout`      | `60.0`                   | Per-request timeout in seconds            |
| `max_retries`  | `3`                      | Retries for 429/5xx (exponential backoff) |
| `user_agent`   | `ambie-python/<version>` | Sent on every request                     |
| `http_client`  | `httpx.Client(...)`      | Inject a custom client (proxy, certs)     |

## Error handling

```python
from ambie import AmbieError

try:
    c.transcribe(url="not-a-url")
except AmbieError as e:
    print(e.status, e.code, e.message, e.request_id)
```

## Coverage

Supported endpoints: `transcribe`, `translate`, `tts`, `sentiment`, `summarize`, `embeddings`, `rerank`, `moderate`, `detect_language`. Each has a sync POST and async polling via `get_<endpoint>_job(request_id)`.

See the full [OpenAPI 3.1 spec](https://ambie.ai/openapi.yaml).

## License

MIT © AMBIE
