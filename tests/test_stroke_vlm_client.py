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

    # Inspect the images argument (passed as keyword argument)
    call_kwargs = mock_multi.call_args
    images: list[tuple[bytes, str]] = (
        call_kwargs.kwargs.get("images") or call_kwargs.args[1]
    )

    assert len(images) == 11, (
        f"Expected 11 images (1 canvas + 10 samples), got {len(images)}"
    )

    # First entry must be the current canvas
    assert images[0][1] == "Current canvas", (
        f"First image label should be 'Current canvas', got '{images[0][1]}'"
    )

    # Remaining 5 labels must be the stroke sample labels
    sample_labels = {label for _, label in images[1:]}
    assert sample_labels == _EXPECTED_SAMPLE_LABELS, (
        f"Sample labels mismatch. Expected {_EXPECTED_SAMPLE_LABELS}, got {sample_labels}"
    )


def test_prompt_references_samples() -> None:
    """_build_stroke_prompt() includes visual sample references for every stroke type.

    Verifies that the returned prompt string contains the label strings that
    match the images sent via ``query_multimodal_multi_image``.
    """
    client = StrokeVLMClient()

    prompt = client._build_stroke_prompt(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )

    for label in _EXPECTED_SAMPLE_LABELS:
        assert label in prompt, f"Prompt should contain '{label}' but it was not found"


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
    assert images[0][1] == "Current canvas", (
        f"First image label should be 'Current canvas', got '{images[0][1]}'"
    )
    assert images[1][1] == "LINE stroke sample", (
        f"Second image label should be 'LINE stroke sample', got '{images[1][1]}'"
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
    sample_labels = {label for _, label in images[1:]}
    assert sample_labels == _EXPECTED_SAMPLE_LABELS, (
        f"Sample labels mismatch. Expected {_EXPECTED_SAMPLE_LABELS}, got {sample_labels}"
    )
