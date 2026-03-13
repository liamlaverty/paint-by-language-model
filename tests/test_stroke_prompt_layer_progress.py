"""Tests for the LAYER PROGRESS section injected into stroke prompts."""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import MIN_STROKES_PER_LAYER
from models.painting_plan import PaintingPlan, PlanLayer
from services.clients.stroke_vlm_client import StrokeVLMClient

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _make_layer(layer_number: int = 1) -> PlanLayer:
    """Return a minimal PlanLayer suitable for prompt building tests."""
    return PlanLayer(
        layer_number=layer_number,
        name=f"Layer {layer_number}",
        description=f"Test description for layer {layer_number}",
        colour_palette=["#FF0000", "#00FF00"],
        stroke_types=["line"],
        techniques="Test techniques",
        shapes="Test shapes",
        highlights="Test highlights",
    )


def _make_plan(num_layers: int = 2) -> PaintingPlan:
    """Return a minimal PaintingPlan with the requested number of layers."""
    layers = [_make_layer(i + 1) for i in range(num_layers)]
    return PaintingPlan(
        artist_name="Test Artist",
        subject="Test Subject",
        expanded_subject=None,
        total_layers=num_layers,
        layers=layers,
        overall_notes="Test notes",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_layer_progress_below_minimum_blocks_completion() -> None:
    """Prompt tells VLM it must NOT signal completion when below minimum.

    When layer_iteration_count is less than MIN_STROKES_PER_LAYER the
    LAYER PROGRESS section must instruct the VLM not to set layer_complete.
    """
    client = StrokeVLMClient()
    plan = _make_plan()
    layer = plan["layers"][0]

    prompt = client._build_stroke_prompt(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=3,
        strategy_context="",
        num_strokes=5,
        painting_plan=plan,
        current_layer=layer,
        layer_iteration_count=3,  # below MIN_STROKES_PER_LAYER
    )

    assert "Do NOT set layer_complete to true yet" in prompt


def test_layer_progress_at_minimum_allows_completion() -> None:
    """Prompt tells VLM it MAY signal completion once minimum is reached."""
    client = StrokeVLMClient()
    plan = _make_plan()
    layer = plan["layers"][0]

    prompt = client._build_stroke_prompt(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=MIN_STROKES_PER_LAYER,
        strategy_context="",
        num_strokes=5,
        painting_plan=plan,
        current_layer=layer,
        layer_iteration_count=MIN_STROKES_PER_LAYER,
    )

    assert "You may signal layer_complete: true" in prompt
    assert "Do NOT set layer_complete to true yet" not in prompt


def test_layer_progress_above_minimum_allows_completion() -> None:
    """Prompt allows completion when iteration count exceeds minimum."""
    client = StrokeVLMClient()
    plan = _make_plan()
    layer = plan["layers"][0]

    prompt = client._build_stroke_prompt(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=MIN_STROKES_PER_LAYER + 5,
        strategy_context="",
        num_strokes=5,
        painting_plan=plan,
        current_layer=layer,
        layer_iteration_count=MIN_STROKES_PER_LAYER + 5,
    )

    assert "You may signal layer_complete: true" in prompt
    assert "Do NOT set layer_complete to true yet" not in prompt


def test_layer_progress_shows_correct_iteration_number() -> None:
    """Prompt reports the exact iteration count passed in."""
    client = StrokeVLMClient()
    plan = _make_plan()
    layer = plan["layers"][0]
    count = 7

    prompt = client._build_stroke_prompt(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=count,
        strategy_context="",
        num_strokes=5,
        painting_plan=plan,
        current_layer=layer,
        layer_iteration_count=count,
    )

    assert f"You are currently on iteration {count} of this layer" in prompt


def test_no_layer_progress_section_without_plan() -> None:
    """Prompt must NOT include LAYER PROGRESS when no painting plan is active."""
    client = StrokeVLMClient()

    prompt = client._build_stroke_prompt(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=1,
        strategy_context="",
        num_strokes=5,
        painting_plan=None,
        current_layer=None,
        layer_iteration_count=0,
    )

    assert "LAYER PROGRESS" not in prompt
