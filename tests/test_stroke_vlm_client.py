"""Unit tests for StrokeVLMClient."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.clients.stroke_vlm_client import StrokeVLMClient

# ============================================================================
# Helpers

_VALID_STROKE_JSON = json.dumps(
    {
        "strokes": [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 20,
                "end_x": 30,
                "end_y": 40,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 0.8,
            }
        ],
        "updated_strategy": None,
        "batch_reasoning": "Test batch reasoning",
    }
)

_EXPECTED_SAMPLE_LABELS = {
    "LINE stroke sample",
    "ARC stroke sample",
    "POLYLINE stroke sample",
    "CIRCLE stroke sample",
    "SPLATTER stroke sample",
    "DRY-BRUSH stroke sample",
    "CHALK stroke sample",
    "WET-BRUSH stroke sample",
    "BURN stroke sample",
    "DODGE stroke sample",
}

# ============================================================================
# Tests
# ============================================================================


def test_sample_generator_initialized_at_init() -> None:
    """StrokeVLMClient eagerly generates all stroke samples on construction.

    Verifies that ``_stroke_samples`` is populated with exactly 10 keys
    (one per supported stroke type) when the client is constructed.
    """
    client = StrokeVLMClient()

    assert isinstance(client._stroke_samples, dict), "_stroke_samples should be a dict"
    assert len(client._stroke_samples) == 10, (
        f"Expected 10 stroke samples, got {len(client._stroke_samples)}"
    )


def test_suggest_strokes_sends_sample_images() -> None:
    """suggest_strokes() calls query_multimodal_multi_image with canvas + 9 sample images.

    Verifies:
    - ``query_multimodal_multi_image`` is called (not ``query_multimodal``)
        - The ``images`` argument contains exactly 11 entries (1 canvas + 10 samples)
    - The first image label is ``"Current canvas""
    - The remaining labels match the expected stroke sample names
    - ``system_prompt`` keyword argument is passed
    """
    client = StrokeVLMClient()

    with (
        patch.object(
            client.client,
            "query_multimodal_multi_image",
            return_value=_VALID_STROKE_JSON,
        ) as mock_multi,
        patch.object(
            client.client,
            "query_multimodal",
        ) as mock_single,
    ):
        client.suggest_strokes(
            canvas_image=b"fake_canvas_bytes",
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
        )

    # multi-image method must have been called; single-image must not
    mock_multi.assert_called_once()
    mock_single.assert_not_called()

    # system_prompt keyword arg must be present and non-empty
    call_kwargs = mock_multi.call_args.kwargs
    assert "system_prompt" in call_kwargs, (
        "query_multimodal_multi_image must be called with system_prompt= kwarg"
    )
    assert isinstance(call_kwargs["system_prompt"], str)
    assert len(call_kwargs["system_prompt"]) > 0

    # Inspect the images argument (passed as keyword argument)
    images: list[tuple[bytes, str]] = (
        call_kwargs.get("images") or mock_multi.call_args.args[1]
    )

    assert len(images) == 11, (
        f"Expected 11 images (1 canvas + 10 samples), got {len(images)}"
    )

    # Last entry must be the current canvas
    assert images[-1][1] == "Current canvas", (
        f"Last image label should be 'Current canvas', got '{images[-1][1]}'"
    )

    # First 10 labels must be the stroke sample labels
    sample_labels = {label for _, label in images[:-1]}
    assert sample_labels == _EXPECTED_SAMPLE_LABELS, (
        f"Sample labels mismatch. Expected {_EXPECTED_SAMPLE_LABELS}, got {sample_labels}"
    )


def test_prompt_references_samples() -> None:
    """_build_stroke_prompts() system prompt includes visual sample references for every stroke type.

    Verifies that the returned system prompt string contains the label strings that
    match the images sent via ``query_multimodal_multi_image``.
    """
    client = StrokeVLMClient()

    system_prompt, _user_prompt = client._build_stroke_prompts(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )

    for label in _EXPECTED_SAMPLE_LABELS:
        assert label in system_prompt, (
            f"System prompt should contain '{label}' but it was not found"
        )


# ============================================================================
# Tests for _build_stroke_types_section filtering
# ============================================================================

_ALL_TEN_TYPES = [
    "LINE",
    "ARC",
    "POLYLINE",
    "CIRCLE",
    "SPLATTER",
    "DRY-BRUSH",
    "CHALK",
    "WET-BRUSH",
    "BURN",
    "DODGE",
]


def test_stroke_types_section_filters_to_allowed_types() -> None:
    """_build_stroke_types_section() only includes allowed stroke types.

    When ``allowed_stroke_types=["line", "circle"]`` is set, the returned
    section must contain LINE and CIRCLE entries and must not contain any of
    the other eight type names.
    """
    client = StrokeVLMClient(allowed_stroke_types=["line", "circle"])
    section = client._build_stroke_types_section()

    assert "LINE" in section, "Section should contain LINE"
    assert "CIRCLE" in section, "Section should contain CIRCLE"

    excluded = [
        "ARC",
        "POLYLINE",
        "SPLATTER",
        "DRY-BRUSH",
        "CHALK",
        "WET-BRUSH",
        "BURN",
        "DODGE",
    ]
    for excluded_type in excluded:
        assert excluded_type not in section, (
            f"Section should NOT contain {excluded_type} when it is not in allowed_stroke_types"
        )


def test_stroke_types_section_renumbers_sequentially() -> None:
    """_build_stroke_types_section() re-numbers filtered entries without gaps.

    With ``allowed_stroke_types=["line", "circle"]`` the two entries should be
    numbered 1 and 2 with no gaps.
    """
    client = StrokeVLMClient(allowed_stroke_types=["line", "circle"])
    section = client._build_stroke_types_section()

    assert "1. LINE" in section, "First entry should be numbered 1"
    assert "2. CIRCLE" in section, "Second entry should be numbered 2"


def test_stroke_types_section_all_types_when_none() -> None:
    """_build_stroke_types_section() returns all ten types when allowed_stroke_types is None.

    Preserves backward-compatibility: callers that do not specify
    ``allowed_stroke_types`` should see all ten stroke types in the section.
    """
    client = StrokeVLMClient()  # allowed_stroke_types defaults to None
    section = client._build_stroke_types_section()

    for stroke_type in _ALL_TEN_TYPES:
        assert stroke_type in section, (
            f"Section should contain {stroke_type} when allowed_stroke_types is None"
        )


# ============================================================================
# Tests for sample image filtering
# ============================================================================


def test_suggest_strokes_filters_samples_to_allowed_type() -> None:
    """suggest_strokes() only attaches sample images for allowed stroke types.

    When ``allowed_stroke_types=["line"]`` is set, exactly one sample image
    (the LINE sample) should be appended beyond the canvas image, giving a total
    of 2 entries in the ``images`` argument passed to
    ``query_multimodal_multi_image``.
    """
    client = StrokeVLMClient(allowed_stroke_types=["line"])

    with patch.object(
        client.client,
        "query_multimodal_multi_image",
        return_value=_VALID_STROKE_JSON,
    ) as mock_multi:
        client.suggest_strokes(
            canvas_image=b"fake_canvas_bytes",
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
        )

    mock_multi.assert_called_once()
    call_kwargs = mock_multi.call_args
    images: list[tuple[bytes, str]] = (
        call_kwargs.kwargs.get("images") or call_kwargs.args[1]
    )

    assert len(images) == 2, (
        f"Expected 2 images (1 canvas + 1 allowed sample), got {len(images)}"
    )
    assert images[0][1] == "LINE stroke sample", (
        f"First image label should be 'LINE stroke sample', got '{images[0][1]}'"
    )
    assert images[-1][1] == "Current canvas", (
        f"Last image label should be 'Current canvas', got '{images[-1][1]}'"
    )


def test_suggest_strokes_sends_all_samples_when_allowed_none() -> None:
    """suggest_strokes() attaches all sample images when allowed_stroke_types is None.

    When no ``allowed_stroke_types`` restriction is set (the default), all ten
    stroke sample images should be attached giving 11 total (canvas + 10 samples).
    """
    client = StrokeVLMClient()  # allowed_stroke_types defaults to None

    with patch.object(
        client.client,
        "query_multimodal_multi_image",
        return_value=_VALID_STROKE_JSON,
    ) as mock_multi:
        client.suggest_strokes(
            canvas_image=b"fake_canvas_bytes",
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
        )

    mock_multi.assert_called_once()
    call_kwargs = mock_multi.call_args
    images: list[tuple[bytes, str]] = (
        call_kwargs.kwargs.get("images") or call_kwargs.args[1]
    )

    assert len(images) == 11, (
        f"Expected 11 images (1 canvas + 10 samples), got {len(images)}"
    )
    sample_labels = {label for _, label in images[:-1]}
    assert sample_labels == _EXPECTED_SAMPLE_LABELS, (
        f"Sample labels mismatch. Expected {_EXPECTED_SAMPLE_LABELS}, got {sample_labels}"
    )


# ============================================================================
# Task 3: _build_stroke_prompts new tests
# ============================================================================


def test_build_stroke_prompts_returns_tuple() -> None:
    """_build_stroke_prompts() returns a (system_prompt, user_prompt) tuple."""
    client = StrokeVLMClient()
    result = client._build_stroke_prompts(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )
    assert isinstance(result, tuple), "_build_stroke_prompts must return a tuple"
    assert len(result) == 2, "_build_stroke_prompts must return exactly 2 elements"
    system_prompt, user_prompt = result
    assert isinstance(system_prompt, str)
    assert isinstance(user_prompt, str)


def test_build_stroke_prompts_system_contains_artist_persona() -> None:
    """System prompt contains artist persona line."""
    client = StrokeVLMClient()
    system_prompt, _user = client._build_stroke_prompts(
        artist_name="Monet",
        subject="Water Lilies",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )
    assert "Monet" in system_prompt, "Artist name must appear in system prompt"


def test_build_stroke_prompts_system_contains_stroke_type_definitions() -> None:
    """System prompt contains stroke type definitions."""
    client = StrokeVLMClient()
    system_prompt, _user = client._build_stroke_prompts(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )
    assert "AVAILABLE STROKE TYPES:" in system_prompt


def test_build_stroke_prompts_user_contains_iteration() -> None:
    """User prompt contains the iteration number."""
    client = StrokeVLMClient()
    _system, user_prompt = client._build_stroke_prompts(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=42,
        strategy_context="",
        num_strokes=3,
    )
    assert "42" in user_prompt, "Iteration number must appear in user prompt"


def test_build_stroke_prompts_user_contains_subject() -> None:
    """User prompt contains the subject."""
    client = StrokeVLMClient()
    _system, user_prompt = client._build_stroke_prompts(
        artist_name="Test Artist",
        subject="A Sunny Meadow",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )
    assert "A Sunny Meadow" in user_prompt


def test_build_stroke_prompts_response_format_not_in_user_prompt() -> None:
    """JSON RESPONSE FORMAT spec is NOT in the user prompt (it belongs in system)."""
    client = StrokeVLMClient()
    _system, user_prompt = client._build_stroke_prompts(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )
    assert "RESPONSE FORMAT" not in user_prompt


def test_system_prompt_byte_identical_across_consecutive_calls() -> None:
    """System prompt is byte-identical across two consecutive _build_stroke_prompts calls.

    Proves cacheability: for a fixed artist + stroke config the system content
    must be deterministic so Anthropic's ephemeral cache can be hit on the second call.
    """
    client = StrokeVLMClient()

    system1, _user1 = client._build_stroke_prompts(
        artist_name="Rembrandt",
        subject="Night Watch",
        iteration=1,
        strategy_context="",
        num_strokes=5,
    )
    system2, _user2 = client._build_stroke_prompts(
        artist_name="Rembrandt",
        subject="Night Watch",
        iteration=2,  # different iteration — user prompt differs, system must not
        strategy_context="Add more shadows",
        num_strokes=5,
    )

    assert system1 == system2, (
        "System prompt must be byte-identical across calls for the same artist config"
    )
