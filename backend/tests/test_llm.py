import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import suggest_tags, _make_prompt, _parse_response, SYSTEM_PROMPT


def test_make_prompt_with_all_data():
    """Test prompt building with complete track data."""
    prompt = _make_prompt(
        name="Hypnotic Journey",
        artist="Dark Ambient Artist",
        label="Hypnus Records",
        bpm=132,
        key="8A",
    )

    assert "Hypnotic Journey" in prompt
    assert "Dark Ambient Artist" in prompt
    assert "Hypnus Records" in prompt
    assert "132" in prompt
    assert "8A" in prompt
    assert "Camelot" in prompt


def test_make_prompt_without_label():
    """Test prompt when label is not provided."""
    prompt = _make_prompt(
        name="Track",
        artist="Artist",
        label=None,
        bpm=130,
        key="7B",
    )

    assert "Label n'est pas fourni" in prompt or "label n'est pas fourni" in prompt.lower()


def test_make_prompt_without_bpm():
    """Test prompt when BPM is not provided."""
    prompt = _make_prompt(
        name="Track",
        artist="Artist",
        label="Label",
        bpm=None,
        key="7B",
    )

    assert "BPM n'est pas fourni" in prompt or "bpm n'est pas fourni" in prompt.lower()


def test_make_prompt_minimal():
    """Test prompt with only name and artist."""
    prompt = _make_prompt(
        name="Track",
        artist="Artist",
        label=None,
        bpm=None,
        key=None,
    )

    assert "Track" in prompt
    assert "Artist" in prompt
    assert "[GRAIN]" in prompt or "GRAIN" in prompt


def test_parse_response_valid_json():
    """Test parsing valid JSON response from LLM."""
    response_text = """{
        "bpm_estimate": 132,
        "label_suggestions": ["Hypnus", "Northern"],
        "grain": "aquatique",
        "grain_reasoning": "Deep texture",
        "sensations": ["hypnotique"],
        "sensations_reasoning": "Trance-inducing",
        "masse_basse": "lourd",
        "masse_basse_reasoning": "Heavy kick",
        "role_set": "peak_time",
        "role_set_reasoning": "Peak energy",
        "layering_note": "Poetic description",
        "reasoning": "Overall summary"
    }"""

    result = _parse_response(response_text)

    assert result["bpm_estimate"] == 132
    assert result["grain"] == "aquatique"
    assert result["sensations"] == ["hypnotique"]
    assert len(result["label_suggestions"]) == 2


def test_parse_response_with_markdown():
    """Test parsing response wrapped in markdown code blocks."""
    response_text = """```json
    {
        "bpm_estimate": 128,
        "label_suggestions": [],
        "grain": "poussiéreux",
        "grain_reasoning": "Grainy texture",
        "sensations": [],
        "sensations_reasoning": "Minimal",
        "masse_basse": null,
        "masse_basse_reasoning": "No kick",
        "role_set": "planage",
        "role_set_reasoning": "Ambient drift",
        "layering_note": "Ambient pad",
        "reasoning": "Summary"
    }
    ```"""

    result = _parse_response(response_text)

    assert result["bpm_estimate"] == 128
    assert result["grain"] == "poussiéreux"
    assert result["masse_basse"] is None


def test_parse_response_null_values():
    """Test parsing response with null fields."""
    response_text = """{
        "bpm_estimate": null,
        "label_suggestions": [],
        "grain": null,
        "grain_reasoning": "Unknown",
        "sensations": [],
        "sensations_reasoning": "No sensations",
        "masse_basse": null,
        "masse_basse_reasoning": "Unknown",
        "role_set": null,
        "role_set_reasoning": "Unknown",
        "layering_note": null,
        "reasoning": "Cannot determine"
    }"""

    result = _parse_response(response_text)

    assert result["bpm_estimate"] is None
    assert result["grain"] is None
    assert result["sensations"] == []


@pytest.mark.asyncio
async def test_suggest_tags_success(sample_ai_suggestion):
    """Test successful tag suggestion from LLM."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(sample_ai_suggestion)
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    with patch("llm.genai.GenerativeModel", return_value=mock_model):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            result = await suggest_tags(
                name="Hypnotic Journey",
                artist="Dark Ambient Artist",
                label="Hypnus Records",
                bpm=132,
                key="8A",
            )

            assert result["grain"] == "aquatique"
            assert "hypnotique" in result["sensations"]
            assert result["masse_basse"] == "lourd"
            assert result["role_set"] == "peak_time"
            assert result["bpm_estimate"] == 132


@pytest.mark.asyncio
async def test_suggest_tags_missing_api_key():
    """Test that missing GEMINI_API_KEY raises ValueError."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            await suggest_tags(
                name="Track",
                artist="Artist",
                label=None,
                bpm=None,
                key=None,
            )


@pytest.mark.asyncio
async def test_suggest_tags_minimal_input():
    """Test tag suggestion with only name and artist."""
    mock_response_data = {
        "bpm_estimate": None,
        "label_suggestions": [],
        "grain": "épuré",
        "grain_reasoning": "Minimal aesthetic",
        "sensations": [],
        "sensations_reasoning": "None",
        "masse_basse": None,
        "masse_basse_reasoning": "Unclear",
        "role_set": None,
        "role_set_reasoning": "Unclear",
        "layering_note": "Sparse ambient",
        "reasoning": "Minimal track",
    }

    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_response_data)
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    with patch("llm.genai.GenerativeModel", return_value=mock_model):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            result = await suggest_tags(
                name="Minimal Track",
                artist="Artist",
            )

            assert result["grain"] == "épuré"
            assert result["bpm_estimate"] is None


@pytest.mark.asyncio
async def test_suggest_tags_with_bpm_in_reasoning():
    """Test that BPM is included in the prompt for reasoning."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    ai_result = {
        "bpm_estimate": 132,
        "label_suggestions": [],
        "grain": "saturé",
        "grain_reasoning": "Heavy, compressed sound at 132 BPM",
        "sensations": ["nerveux"],
        "sensations_reasoning": "Fast-moving elements",
        "masse_basse": "lourd",
        "masse_basse_reasoning": "Deep kick at 132 BPM creates foundation",
        "role_set": "peak_time",
        "role_set_reasoning": "High energy at 132 BPM",
        "layering_note": "Heavy baseline",
        "reasoning": "At 132 BPM, this is peak material",
    }
    mock_response.text = json.dumps(ai_result)
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    with patch("llm.genai.GenerativeModel", return_value=mock_model):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            result = await suggest_tags(
                name="Heavy Peak",
                artist="Techno Artist",
                bpm=132,
            )

            # Verify BPM is included in reasoning
            assert "132" in result["masse_basse_reasoning"]
            assert "132" in result["role_set_reasoning"]


def test_system_prompt_contains_vocabulary():
    """Test that system prompt includes vocabulary context."""
    assert "sensations" in SYSTEM_PROMPT.lower()
    assert "masse" in SYSTEM_PROMPT.lower()
    assert "Swamp Stage" in SYSTEM_PROMPT or "Mo:Dem" in SYSTEM_PROMPT


def test_system_prompt_labels_not_source():
    """Test that system prompt clarifies reference labels are not source."""
    assert "n'est pas forcément" in SYSTEM_PROMPT or "ne viennent pas" in SYSTEM_PROMPT.lower()
