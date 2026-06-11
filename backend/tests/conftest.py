import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiosqlite
import httpx


@pytest.fixture
def mock_db():
    """Mock aiosqlite connection."""
    db = AsyncMock(spec=aiosqlite.Connection)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.close = AsyncMock()
    db.cursor = AsyncMock()
    return db


@pytest.fixture
def mock_cursor():
    """Mock cursor for database operations."""
    cursor = AsyncMock()
    cursor.fetchone = AsyncMock()
    cursor.fetchall = AsyncMock()
    cursor.lastrowid = 123
    return cursor


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for external API calls."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.patch = AsyncMock()
    client.delete = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.fixture
def mock_genai_model():
    """Mock google.generativeai.GenerativeModel."""
    model = MagicMock()
    model.generate_content_async = AsyncMock()
    return model


@pytest.fixture
def sample_track():
    """Sample track data for testing."""
    return {
        "id": 1,
        "notion_id": "notion-123",
        "name": "Hypnotic Journey",
        "artist": "Dark Ambient Artist",
        "album": "Deep Sessions",
        "label": "Hypnus Records",
        "bpm": 132,
        "key": "8A",
        "grain": "aquatique",
        "sensations": ["hypnotique", "mystérieux"],
        "masse_basse": "lourd",
        "role_set": "peak_time",
        "url": "https://spotify.com/track/abc123",
        "downloaded": True,
        "notes": "Great for layering",
        "layering": "Deep foundation track",
    }


@pytest.fixture
def sample_spotify_meta():
    """Sample Spotify metadata response."""
    return {
        "name": "Hypnotic Journey",
        "artist": "Dark Ambient Artist",
        "label": "Hypnus Records",
        "url": "https://open.spotify.com/track/abc123",
        "image_url": "https://i.scdn.co/image/123",
        "bpm": 132,
        "key": "8A",
    }


@pytest.fixture
def sample_ai_suggestion():
    """Sample AI suggestion response."""
    return {
        "bpm_estimate": 132,
        "label_suggestions": ["Hypnus Records", "Northern Electronics"],
        "grain": "aquatique",
        "grain_reasoning": "Dark, aqueous texture with minimal percussion creates a liquid, immersive soundscape.",
        "sensations": ["hypnotique", "mystérieux"],
        "sensations_reasoning": "Repetitive patterns and ethereal pads induce hypnotic trance; atmospheric elements create mystery.",
        "masse_basse": "lourd",
        "masse_basse_reasoning": "Kick is deep and powerful, anchoring the mix at 132 BPM.",
        "role_set": "peak_time",
        "role_set_reasoning": "Energy builds toward climax; suitable for peak moment around 132 BPM.",
        "layering_note": "A deep, meditative journey through ethereal textures and grounded kick work. Layer beneath atmospheric pads for dreamlike builds.",
        "reasoning": "Strong hypnotic dark ambient track with cinematic qualities. Perfect for opening extended sets.",
    }


@pytest.fixture
def sample_notion_page():
    """Sample Notion database page structure."""
    return {
        "id": "notion-page-123",
        "properties": {
            "Name": {"title": [{"text": {"content": "Hypnotic Journey"}, "plain_text": "Hypnotic Journey"}]},
            "Artist": {"rich_text": [{"text": {"content": "Dark Ambient Artist"}, "plain_text": "Dark Ambient Artist"}]},
            "BPM": {"number": 132},
            "Key": {"rich_text": [{"text": {"content": "8A"}, "plain_text": "8A"}]},
            "Label": {"select": {"name": "Hypnus Records"}},
            "Grain": {"select": {"name": "Aquatique (Liquide / Profond)"}},
            "Sensations": {
                "multi_select": [
                    {"name": "Hypnotique (L'Aspiration)"},
                    {"name": "Mystérieux (Profond)"}
                ]
            },
            "Masse Basse": {"select": {"name": "Lourd / Brrr (La Masse)"}},
            "Role Set": {"select": {"name": "3. Peak Time (Lourdeur/Brrr)"}},
            "URL": {"url": "https://open.spotify.com/track/abc123"},
            "Downloaded": {"checkbox": True},
            "Layering": {"rich_text": [{"text": {"content": "Deep foundation track"}, "plain_text": "Deep foundation track"}]},
        },
    }
