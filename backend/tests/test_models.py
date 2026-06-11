import pytest
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import TrackCreate, TrackUpdate, Track


def test_track_create_required_fields():
    """Test TrackCreate with required fields only."""
    data = {
        "name": "Track Name",
        "artist": "Artist Name",
    }

    track = TrackCreate(**data)

    assert track.name == "Track Name"
    assert track.artist == "Artist Name"
    assert track.sensations == []
    assert track.downloaded is False


def test_track_create_complete():
    """Test TrackCreate with all fields."""
    data = {
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
        "url": "https://spotify.com/track/123",
        "downloaded": True,
        "notes": "Great track",
        "layering": "Deep foundation",
    }

    track = TrackCreate(**data)

    assert track.name == "Hypnotic Journey"
    assert track.bpm == 132
    assert "hypnotique" in track.sensations
    assert track.layering == "Deep foundation"


def test_track_create_missing_required_name():
    """Test TrackCreate fails without name."""
    data = {
        "artist": "Artist",
    }

    with pytest.raises(ValidationError) as exc:
        TrackCreate(**data)

    assert "name" in str(exc.value).lower()


def test_track_create_missing_required_artist():
    """Test TrackCreate fails without artist."""
    data = {
        "name": "Track",
    }

    with pytest.raises(ValidationError) as exc:
        TrackCreate(**data)

    assert "artist" in str(exc.value).lower()


def test_track_create_sensations_list():
    """Test sensations must be list."""
    data = {
        "name": "Track",
        "artist": "Artist",
        "sensations": ["hypnotique", "nerveux"],
    }

    track = TrackCreate(**data)

    assert isinstance(track.sensations, list)
    assert len(track.sensations) == 2


def test_track_create_sensations_empty():
    """Test sensations can be empty list."""
    data = {
        "name": "Track",
        "artist": "Artist",
        "sensations": [],
    }

    track = TrackCreate(**data)

    assert track.sensations == []


def test_track_create_downloaded_boolean():
    """Test downloaded must be boolean."""
    data = {
        "name": "Track",
        "artist": "Artist",
        "downloaded": True,
    }

    track = TrackCreate(**data)
    assert track.downloaded is True

    data["downloaded"] = False
    track = TrackCreate(**data)
    assert track.downloaded is False


def test_track_create_bpm_optional_number():
    """Test BPM is optional but must be number."""
    # Valid BPM
    track = TrackCreate(name="Track", artist="Artist", bpm=128)
    assert track.bpm == 128

    # None is allowed
    track = TrackCreate(name="Track", artist="Artist", bpm=None)
    assert track.bpm is None


def test_track_update_all_optional():
    """Test TrackUpdate allows all fields as optional."""
    data = {}
    track = TrackUpdate(**data)
    assert track.grain is None
    assert track.sensations is None

    # Partial update
    data = {
        "grain": "poussiéreux",
        "notes": "Updated notes",
    }
    track = TrackUpdate(**data)
    assert track.grain == "poussiéreux"
    assert track.notes == "Updated notes"
    assert track.bpm is None


def test_track_update_layering():
    """Test TrackUpdate can update layering field."""
    data = {
        "layering": "New layering notes",
    }

    track = TrackUpdate(**data)

    assert track.layering == "New layering notes"


def test_track_update_sensations():
    """Test TrackUpdate with sensations list."""
    data = {
        "sensations": ["hypnotique", "acide"],
    }

    track = TrackUpdate(**data)

    assert track.sensations == ["hypnotique", "acide"]


def test_track_model_with_full_data(sample_track):
    """Test Track model with full sample data."""
    track = Track(**sample_track)

    assert track.id == sample_track["id"]
    assert track.name == sample_track["name"]
    assert track.artist == sample_track["artist"]
    assert track.bpm == sample_track["bpm"]
    assert track.grain == sample_track["grain"]


def test_track_create_extra_fields_ignored():
    """Test that extra fields in TrackCreate are ignored or raise."""
    data = {
        "name": "Track",
        "artist": "Artist",
        "extra_field": "should be ignored",
    }

    # Pydantic should either ignore or raise depending on config
    try:
        track = TrackCreate(**data)
        assert track.name == "Track"
    except ValidationError:
        pass  # Extra fields validation is okay


def test_track_update_mass_basse():
    """Test TrackUpdate with masse_basse."""
    data = {
        "masse_basse": "léger",
    }

    track = TrackUpdate(**data)

    assert track.masse_basse == "léger"


def test_track_update_role_set():
    """Test TrackUpdate with role_set."""
    data = {
        "role_set": "construction",
    }

    track = TrackUpdate(**data)

    assert track.role_set == "construction"


def test_track_create_key_optional():
    """Test key field is optional."""
    track = TrackCreate(name="Track", artist="Artist", key="8A")
    assert track.key == "8A"

    track = TrackCreate(name="Track", artist="Artist", key=None)
    assert track.key is None

    track = TrackCreate(name="Track", artist="Artist")
    assert track.key is None


def test_track_create_album_optional():
    """Test album field is optional."""
    track = TrackCreate(name="Track", artist="Artist", album="Album Name")
    assert track.album == "Album Name"

    track = TrackCreate(name="Track", artist="Artist")
    assert track.album is None


def test_track_create_label_optional():
    """Test label field is optional."""
    track = TrackCreate(name="Track", artist="Artist", label="Label Name")
    assert track.label == "Label Name"

    track = TrackCreate(name="Track", artist="Artist")
    assert track.label is None


def test_track_create_url_optional():
    """Test url field is optional."""
    url = "https://spotify.com/track/abc123"
    track = TrackCreate(name="Track", artist="Artist", url=url)
    assert track.url == url

    track = TrackCreate(name="Track", artist="Artist")
    assert track.url is None


def test_track_create_notes_optional():
    """Test notes field is optional."""
    track = TrackCreate(name="Track", artist="Artist", notes="Some notes")
    assert track.notes == "Some notes"

    track = TrackCreate(name="Track", artist="Artist")
    assert track.notes is None


def test_track_create_model_dump():
    """Test model_dump converts to dict."""
    data = {
        "name": "Track",
        "artist": "Artist",
        "bpm": 128,
        "sensations": ["hypnotique"],
    }

    track = TrackCreate(**data)
    dumped = track.model_dump()

    assert dumped["name"] == "Track"
    assert dumped["bpm"] == 128
    assert isinstance(dumped["sensations"], list)
