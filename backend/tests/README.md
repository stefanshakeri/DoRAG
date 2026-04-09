# Backend Test Suite

This directory contains automated tests for the DoRAG backend API.

## Test Files

- `test_auth.py`: authentication endpoints and auth-related behavior.
- `test_users.py`: user profile and user-related routes.
- `test_chatbots.py`: chatbot CRUD and chatbot-related route behavior.
- `test_documents.py`: document upload/list/delete route behavior.
- `test_chat.py`: chat endpoint behavior.
- `conftest.py`: shared fixtures, dependency overrides, and service mocks.

## What the Tests Use

The suite uses:

- `pytest`
- `fastapi.testclient.TestClient`
- `unittest.mock` (`patch`, `AsyncMock`)

`conftest.py` sets safe default environment variables and overrides auth dependencies so tests can run without real external credentials.

## Run Tests

Run from the `backend` directory.

### Run all tests

```bash
pytest tests -v
```

### Run a single test file

```bash
pytest tests/test_chat.py -v
```

### Run live API tests (real HTTP requests)

These tests call a running backend instance over HTTP using `httpx`.

```bash
RUN_LIVE_API_TESTS=1 DORAG_API_BASE_URL=http://127.0.0.1:8000 pytest tests/test_api_live.py -v
```

Optional environment variables:

- `DORAG_API_TIMEOUT_SECONDS` (default: `10`)
- `DORAG_API_BEARER_TOKEN` to run authenticated checks
- `DORAG_QDRANT_URL` and optional `DORAG_QDRANT_API_KEY` to run live Qdrant request checks
- `DORAG_SUPABASE_URL` and optional `DORAG_SUPABASE_API_KEY` to run live Supabase API checks
- `DORAG_REDIS_HOST`, `DORAG_REDIS_PORT`, optional `DORAG_REDIS_USERNAME`, `DORAG_REDIS_PASSWORD`, and optional `DORAG_REDIS_SSL` to run live Redis connectivity checks

### Run a single test case

```bash
pytest tests/test_chat.py -k "test_name_part" -v
```

## Notes

- External services (Supabase, Qdrant, Redis, OpenAI) are mocked in tests.
- Keep tests deterministic and isolated. Prefer fixtures and mocks over real network calls.
- If you add a new router, add a corresponding `test_*.py` file in this folder.
- Live API tests are opt-in and only run when `RUN_LIVE_API_TESTS=1` is set.
