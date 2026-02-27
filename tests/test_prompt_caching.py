"""Tests covering prompt caching behaviour in StrokeVLMClient and EvaluationVLMClient."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.evaluation_vlm_client import EvaluationVLMClient
from services.stroke_vlm_client import StrokeVLMClient

# ============================================================================
# Shared helpers
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

_VALID_EVALUATION_JSON = json.dumps(
    {
        "score": 75.0,
        "feedback": "Good overall style",
        "strengths": "Colour palette",
        "suggestions": "Add more texture",
    }
)

# ============================================================================
# StrokeVLMClient — static instructions
# ============================================================================


def test_stroke_static_instructions_contains_all_types() -> None:
    """_build_static_stroke_instructions() mentions all five stroke type names."""
    client = StrokeVLMClient()
    instructions = client._build_static_stroke_instructions()

    for stroke_type in ("LINE", "ARC", "POLYLINE", "CIRCLE", "SPLATTER"):
        assert stroke_type in instructions, (
            f"Expected stroke type '{stroke_type}' to appear in static instructions"
        )


def test_stroke_prompt_excludes_static_content() -> None:
    """_build_stroke_prompt() does not contain the stroke type definitions block."""
    client = StrokeVLMClient()
    prompt = client._build_stroke_prompt(
        artist_name="Monet",
        subject="test subject",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )

    # The full stroke type definitions are in the static instructions, not the dynamic prompt
    assert "AVAILABLE STROKE TYPES" not in prompt, (
        "Static 'AVAILABLE STROKE TYPES' section should not appear in the dynamic prompt"
    )


def test_suggest_strokes_passes_system_and_cache_index_to_client() -> None:
    """suggest_strokes() forwards a non-empty system= and valid cache_after_index= to the VLMClient."""
    client = StrokeVLMClient()

    mock_query = MagicMock(return_value=_VALID_STROKE_JSON)
    client.client.query_multimodal_multi_image = mock_query  # type: ignore[method-assign]

    client.suggest_strokes(
        canvas_image=b"fake-canvas",
        artist_name="Monet",
        subject="water lilies",
        iteration=1,
    )

    mock_query.assert_called_once()
    _, kwargs = mock_query.call_args

    # system kwarg must be a non-empty string (the static instructions)
    assert "system" in kwargs, (
        "query_multimodal_multi_image must receive a 'system' kwarg"
    )
    assert isinstance(kwargs["system"], str) and len(kwargs["system"]) > 0, (
        "system kwarg must be a non-empty string"
    )

    # cache_after_index must be a non-negative integer
    assert "cache_after_index" in kwargs, (
        "query_multimodal_multi_image must receive a 'cache_after_index' kwarg"
    )
    assert isinstance(kwargs["cache_after_index"], int), (
        "cache_after_index must be an integer"
    )
    assert kwargs["cache_after_index"] >= 0, "cache_after_index must be >= 0"

    # Specifically: cache_after_index should be len(stroke_samples) - 1
    expected_cache_index = len(client._stroke_samples) - 1
    assert kwargs["cache_after_index"] == expected_cache_index, (
        f"Expected cache_after_index={expected_cache_index}, "
        f"got {kwargs['cache_after_index']}"
    )


# ============================================================================
# EvaluationVLMClient — static instructions
# ============================================================================


def test_evaluation_static_instructions_contains_rubric_and_schema() -> None:
    """_build_static_evaluation_instructions() contains the rubric and JSON schema field."""
    client = EvaluationVLMClient()
    instructions = client._build_static_evaluation_instructions("Monet")

    # Score rubric range
    assert "0-20" in instructions, (
        "Static evaluation instructions must contain the '0-20' rubric range"
    )

    # JSON schema field
    assert "score" in instructions, (
        "Static evaluation instructions must contain the 'score' JSON schema field"
    )


def test_evaluation_prompt_excludes_static_content() -> None:
    """_build_evaluation_prompt() does not embed the rubric or JSON schema."""
    client = EvaluationVLMClient()
    prompt = client._build_evaluation_prompt(
        artist_name="Monet",
        subject="water lilies",
        iteration=1,
    )

    # Rubric text lives only in the static instructions
    assert "0-20 means no resemblance" not in prompt, (
        "Rubric text should not appear in the dynamic evaluation prompt"
    )

    # JSON schema definition lives only in the static instructions
    assert '"score"' not in prompt, (
        "JSON schema field definition should not appear in the dynamic evaluation prompt"
    )


def test_evaluate_style_passes_system_to_client() -> None:
    """evaluate_style() forwards a non-empty system= kwarg to the underlying VLMClient."""
    client = EvaluationVLMClient()

    mock_query = MagicMock(return_value=_VALID_EVALUATION_JSON)
    client.client.query_multimodal = mock_query  # type: ignore[method-assign]

    client.evaluate_style(
        canvas_image=b"fake-canvas",
        artist_name="Monet",
        subject="water lilies",
        iteration=1,
    )

    mock_query.assert_called_once()
    _, kwargs = mock_query.call_args

    # system kwarg must be a non-empty string (the static evaluation instructions)
    assert "system" in kwargs, "query_multimodal must receive a 'system' kwarg"
    assert isinstance(kwargs["system"], str) and len(kwargs["system"]) > 0, (
        "system kwarg must be a non-empty string"
    )
