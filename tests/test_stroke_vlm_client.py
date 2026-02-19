"""Unit tests for StrokeVLMClient."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.stroke_vlm_client import StrokeVLMClient

# ============================================================================
# Helpers
# ============================================================================

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
}

# ============================================================================
# Tests
# ============================================================================


def test_sample_generator_initialized_at_init() -> None:
    """StrokeVLMClient eagerly generates all stroke samples on construction.

    Verifies that ``_stroke_samples`` is populated with exactly 5 keys
    (one per supported stroke type) when the client is constructed.
    """
    client = StrokeVLMClient()

    assert isinstance(client._stroke_samples, dict), "_stroke_samples should be a dict"
    assert len(client._stroke_samples) == 5, (
        f"Expected 5 stroke samples, got {len(client._stroke_samples)}"
    )


def test_suggest_strokes_sends_sample_images() -> None:
    """suggest_strokes() calls query_multimodal_multi_image with canvas + 5 sample images.

    Verifies:
    - ``query_multimodal_multi_image`` is called (not ``query_multimodal``)
    - The ``images`` argument contains exactly 6 entries (1 canvas + 5 samples)
    - The first image label is ``"Current canvas"``
    - The remaining 5 labels match the expected stroke sample names
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

    assert len(images) == 6, (
        f"Expected 6 images (1 canvas + 5 samples), got {len(images)}"
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
