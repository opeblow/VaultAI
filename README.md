# Podcast Intelligence API

Podcast Intelligence API is a FastAPI backend for turning podcast or spoken-audio files into searchable knowledge vaults.

It handles user authentication, audio upload, transcription, summary generation, vector indexing, and context-grounded Q&A over processed episodes.

## What It Does

- Registers and authenticates users with JWT access tokens.
- Uploads podcast/audio files through a protected API.
- Tracks ingestion jobs in the database.
- Transcribes audio with Whisper.
- Applies simple speaker labels to transcript segments.
- Generates podcast summaries with OpenAI.
- Stores transcript chunks in a FAISS vector index.
- Answers questions using only the indexed transcript context.
- Exposes everything through Swagger UI at `/docs`.

## Current Status

The core product loop is working end to end:

1. Register a user.
2. Log in and get an access token.
3. Upload an audio file.
4. Wait for the job to complete.
5. View the podcast summary.
6. Ask questions about the processed episode.

Paystack webhook code exists, but payment flows are not part of the currently verified path.

## Tech Stack

- FastAPI
- SQLAlchemy
- SQLite by default, PostgreSQL-compatible through `DATABASE_URL`
- JWT auth with `python-jose`
- Whisper for transcription
- SentenceTransformers for embeddings
- FAISS for vector search
- OpenAI Chat Completions for summaries and answers
- Pytest for automated tests

## Project Structure

```text
backend/
  main.py              FastAPI app setup and router registration
  auth.py              JWT and password helpers
  config.py            Environment-based settings
  database.py          SQLAlchemy engine/session setup
  models/schemas.py    ORM models and Pydantic schemas
  routers/             Auth, ingest, query, vault, and payment endpoints

ml/
  pipelines/           Podcast ingestion pipeline
  models/              STT, summarization, embeddings, vector search, Q&A
  utils/               Audio and text helpers

tests/
  test_backend.py      API flow tests with a fake ML pipeline
  test_ml_units.py     Lightweight ML utility tests
```

## Requirements

Use Python 3.11. The ML stack is pinned around Python 3.11-compatible wheels to avoid native LLVM build issues.

You also need `ffmpeg` available on PATH for audio processing.

```bash
ffmpeg -version
```

## Setup

Create and activate a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install backend, test, and ML dependencies:

```bash
python -m pip install -r requirements-dev.txt -r requirements-ml.txt
```

Create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key
SUMMARIZER_SYSTEM_PROMPT="You are an expert podcast analyst. Summarize the key insights."
QA_SYSTEM_PROMPT="Answer questions using only the supplied transcript context."
JWT_SECRET_KEY=replace_with_a_long_random_secret
DATABASE_URL=sqlite:///.podcast.db
```

## Run Tests

```bash
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
```

Expected result:

```text
6 passed
```

## Run The API

```bash
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

## Swagger Testing Flow

1. `POST /auth/register`

```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "password123"
}
```

2. `POST /auth/login`

```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

Copy the `access_token`.

3. Click `Authorize` in Swagger and paste the access token.

4. `POST /ingest/upload`

Upload an audio file and set a title.

5. `GET /ingest/jobs/{job_id}`

Confirm the job reaches `completed`.

6. `GET /vaults/`

Find the processed `podcast_id`.

7. `GET /vaults/{podcast_id}/summary`

Confirm summary, language, duration, and speaker count.

8. `POST /query/ask`

```json
{
  "podcast_id": 1,
  "question": "What is this episode about?"
}
```

## Notes

- The speaker labeling is currently heuristic. It assigns speaker names based on pauses, not true diarization.
- Real ingestion requires OpenAI access and may download Whisper and SentenceTransformer models on first run.
- Uploaded audio, generated metadata, and FAISS indexes are stored under `storage/`.
- Runtime files such as `.env`, `.venv`, `.podcast.db`, and `storage/` are ignored by git.
