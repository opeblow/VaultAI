# Issues Fixed

## What Was Broken Before

- Dependencies were incomplete: ML packages like Whisper, OpenAI, FAISS, SentenceTransformers, etc. were missing.
- Python 3.12 caused ML install issues around `llvmlite`/`numba`, so we moved the working env to Python 3.11.
- Upload title handling was broken in the API.
- QA was not loading the selected podcast's saved FAISS vault properly.
- The QA prompt wrapper did not match `QA_SYSTEM_PROMPT`, so it sometimes refused answers incorrectly.
- Tests were not real automated tests; the old test was interactive, hardcoded to a Windows path, and exited during import failures.
- Auth had refresh token schemas/models but no working refresh/logout endpoints.
- `bcrypt 5` broke `passlib`, so we pinned compatible `bcrypt`.
