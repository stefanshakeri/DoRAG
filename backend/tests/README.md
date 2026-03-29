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

### Run a single test case

```bash
pytest tests/test_chat.py -k "test_name_part" -v
```

## Notes

- External services (Supabase, Qdrant, Redis, OpenAI) are mocked in tests.
- Keep tests deterministic and isolated. Prefer fixtures and mocks over real network calls.
- If you add a new router, add a corresponding `test_*.py` file in this folder.
