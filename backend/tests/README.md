# Backend Tests

Unit test suite for Grimoire DJ backend using pytest with async support and mocking.

## Structure

- **conftest.py**: Shared pytest fixtures
  - `mock_db`: Mock aiosqlite connection
  - `mock_cursor`: Mock database cursor
  - `mock_httpx_client`: Mock httpx.AsyncClient for external API calls
  - `mock_genai_model`: Mock google.generativeai.GenerativeModel
  - `sample_track`, `sample_spotify_meta`, `sample_ai_suggestion`, `sample_notion_page`: Test data fixtures

- **test_spotify.py**: Spotify module tests (60+ test cases)
  - Audio features fetching with Camelot notation conversion
  - Track lookup with URL parsing (standard + intl URLs)
  - Error handling (API errors, invalid URLs, missing data)
  - BPM and key extraction from audio features
  - Label extraction from album metadata

- **test_llm.py**: LLM (Gemini) module tests (40+ test cases)
  - Prompt building with variable track data
  - Response parsing (valid JSON, markdown-wrapped, null values)
  - Tag suggestion with complete/minimal input
  - BPM integration in reasoning fields
  - Error handling (missing API key, LLM errors)
  - System prompt validation

- **test_notion_sync.py**: Notion sync module tests (30+ test cases)
  - Notion page to dict conversion (complete + sparse data)
  - Dict to Notion properties conversion (field mapping, select/multi-select)
  - Vocabulary key mapping (grain, sensations, masse_basse, role_set)
  - Sync operations (pull from Notion, push to Notion, update)
  - Local-only field preservation (layering)

- **test_database.py**: Database module tests (25+ test cases)
  - Row to dict conversion (JSON parsing, boolean conversion)
  - Null field handling
  - Sensations list parsing
  - Schema initialization
  - Field preservation and ordering

- **test_models.py**: Pydantic model validation tests (30+ test cases)
  - TrackCreate validation (required/optional fields)
  - TrackUpdate validation (partial updates)
  - Track model with full data
  - Field type validation (int, bool, list, string)
  - Model serialization (model_dump)

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_spotify.py

# Run specific test
pytest tests/test_spotify.py::test_lookup_spotify_track_valid_url

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v

# Run only async tests
pytest -k asyncio
```

## Test Coverage

- **Spotify API integration**: URL parsing, audio features, error handling
- **Notion API integration**: Page conversion, property mapping, sync operations
- **Gemini LLM integration**: Prompt building, response parsing, reasoning fields
- **Database operations**: Row serialization, JSON handling, boolean conversion
- **Pydantic models**: Field validation, type checking, partial updates

## Mocking Strategy

All external API calls are mocked:
- `httpx.AsyncClient` for Spotify and Notion API calls
- `google.generativeai.GenerativeModel` for Gemini API calls
- `aiosqlite.Connection` for database operations
- Fixtures provide realistic sample data (sample_track, sample_spotify_meta, etc.)

This ensures tests run fast and don't depend on external services.

## Next Steps

- Add integration tests that actually call backend endpoints
- Add API endpoint tests (main.py routes)
- Add end-to-end tests with real Notion/Spotify/Gemini if desired
- Add performance benchmarks for critical paths
