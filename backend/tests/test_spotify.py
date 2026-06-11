import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spotify import lookup_spotify_track, _fetch_audio_features, _CAMELOT


@pytest.mark.asyncio
async def test_fetch_audio_features_success(mock_httpx_client):
    """Test successful audio features fetch from Spotify API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "tempo": 132.5,
        "key": 0,
        "mode": 1,
    }
    mock_httpx_client.get.return_value = mock_response

    with patch("spotify.httpx.AsyncClient", return_value=mock_httpx_client):
        result = await _fetch_audio_features("abc123", "fake-token")

        assert result["bpm"] == 132
        assert result["key"] == "8B"  # C Major = 8B
        mock_httpx_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_audio_features_missing_data():
    """Test audio features fetch with missing or invalid data."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "tempo": None,
        "key": 0,
        "mode": 0,
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("spotify.httpx.AsyncClient", return_value=mock_client):
        result = await _fetch_audio_features("abc123", "fake-token")

        assert result["bpm"] is None
        assert result["key"] == "5A"  # Key 0, mode 0 = C Minor = 5A in Camelot


@pytest.mark.asyncio
async def test_fetch_audio_features_api_error(mock_httpx_client):
    """Test audio features fetch with API error."""
    mock_httpx_client.get.side_effect = httpx.HTTPError("API Error")

    with patch("spotify.httpx.AsyncClient", return_value=mock_httpx_client):
        result = await _fetch_audio_features("abc123", "fake-token")

        assert result["bpm"] is None
        assert result["key"] is None


@pytest.mark.asyncio
async def test_lookup_spotify_track_valid_url(sample_spotify_meta):
    """Test valid Spotify track URL parsing."""
    url = "https://open.spotify.com/track/abc123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "Hypnotic Journey",
        "artists": [{"name": "Dark Ambient Artist"}],
        "album": {"id": "album123", "name": "Deep Sessions", "images": [{"url": "https://i.scdn.co/image/123"}]},
        "external_urls": {"spotify": url},
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("spotify.get_spotify_token", new=AsyncMock(return_value="fake-token")):
        with patch("spotify.httpx.AsyncClient", return_value=mock_client):
            with patch("spotify._fetch_audio_features", return_value={"bpm": 132, "key": "8A"}):
                result = await lookup_spotify_track(url)

                assert result["name"] == "Hypnotic Journey"
            assert result["artist"] == "Dark Ambient Artist"
            assert result["bpm"] == 132
            assert result["key"] == "8A"


@pytest.mark.asyncio
async def test_lookup_spotify_track_invalid_url():
    """Test invalid Spotify URL returns None."""
    url = "https://youtube.com/watch?v=abc"

    result = await lookup_spotify_track(url)
    assert result is None


@pytest.mark.asyncio
async def test_lookup_spotify_track_intl_url():
    """Test international Spotify URL parsing."""
    url = "https://open.spotify.com/intl-fr/track/xyz789"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "Test Track",
        "artists": [{"name": "Test Artist"}],
        "album": {"id": "album789", "name": "Test Album", "images": []},
        "external_urls": {"spotify": url},
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("spotify.get_spotify_token", new=AsyncMock(return_value="fake-token")):
        with patch("spotify.httpx.AsyncClient", return_value=mock_client):
            with patch("spotify._fetch_audio_features", return_value={"bpm": 125, "key": "6A"}):
                result = await lookup_spotify_track(url)

                assert result is not None
                assert result["name"] == "Test Track"


@pytest.mark.asyncio
async def test_lookup_spotify_track_api_error():
    """Test API error handling in track lookup."""
    url = "https://open.spotify.com/track/abc123"

    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"access_token": "fake-token"}),
    )
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("spotify.get_spotify_token", new=AsyncMock(return_value="fake-token")):
        with patch("spotify.httpx.AsyncClient", return_value=mock_client):
            result = await lookup_spotify_track(url)

            assert result is None


def test_camelot_notation_coverage():
    """Test Camelot notation mapping covers all keys."""
    # All 24 keys (0-11 in major, 0-11 in minor)
    assert len(_CAMELOT) == 24

    # Test sample keys
    assert _CAMELOT[(0, 1)] == "8B"  # C Major
    assert _CAMELOT[(0, 0)] == "5A"  # C Minor
    assert _CAMELOT[(1, 1)] == "3B"  # C#/D♭ Major
    assert _CAMELOT[(7, 0)] == "6A"  # G Minor


@pytest.mark.asyncio
async def test_lookup_spotify_track_label_extraction():
    """Test that label is correctly extracted from album data."""
    url = "https://open.spotify.com/track/abc123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "Track Name",
        "artists": [{"name": "Artist"}],
        "album": {
            "id": "album456",
            "name": "Album",
            "images": [],
        },
        "label": "Hypnus Records",
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("spotify.get_spotify_token", new=AsyncMock(return_value="fake-token")):
        with patch("spotify.httpx.AsyncClient", return_value=mock_client):
            with patch("spotify._fetch_audio_features", return_value={"bpm": 130, "key": "7B"}):
                result = await lookup_spotify_track(url)

                assert result.get("label") == "Hypnus Records"
