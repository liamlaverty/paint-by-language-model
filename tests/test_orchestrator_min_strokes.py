"""Tests for the minimum-strokes-per-layer enforcement in GenerationOrchestrator."""

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import MIN_STROKES_PER_LAYER
from generation_orchestrator import GenerationOrchestrator
from models import GenerationConfig
from models.painting_plan import PaintingPlan, PlanLayer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_layer(layer_number: int) -> PlanLayer:
    """Return a minimal PlanLayer."""
    return PlanLayer(
        layer_number=layer_number,
        name=f"Layer {layer_number}",
        description=f"Description for layer {layer_number}",
        colour_palette=["#FFFFFF"],
        stroke_types=["line"],
        techniques="broad strokes",
        shapes="horizontal bands",
        highlights="top edge",
    )


def _make_plan(num_layers: int = 2) -> PaintingPlan:
    """Return a minimal PaintingPlan."""
    layers = [_make_layer(i + 1) for i in range(num_layers)]
    return PaintingPlan(
        artist_name="Test Artist",
        subject="Test Subject",
        expanded_subject=None,
        total_layers=num_layers,
        layers=layers,
        overall_notes="",
    )


def _make_stroke_response(layer_complete: bool = False) -> dict[str, Any]:
    """Return a minimal StrokeVLMResponse-compatible dict."""
    return {
        "strokes": [
            {
                "type": "line",
                "start_x": 0,
                "start_y": 0,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#000000",
                "thickness": 2,
                "opacity": 1.0,
            }
        ],
        "batch_reasoning": "test batch",
        "updated_strategy": None,
        "layer_complete": layer_complete,
    }


def _make_evaluation() -> dict[str, Any]:
    """Return a minimal EvaluationResult-compatible dict."""
    return {
        "score": 50.0,
        "feedback": "OK",
        "strengths": "some",
        "suggestions": "none",
        "timestamp": datetime.now().isoformat(),
        "iteration": 1,
    }


def _make_apply_strokes_results() -> list[dict[str, Any]]:
    """Return a minimal apply_strokes result list for one stroke."""
    return [{"success": True, "index": 0, "error": None}]


def _make_test_config() -> GenerationConfig:
    """Return a minimal GenerationConfig suitable for unit tests."""
    return GenerationConfig(
        provider="lmstudio",
        api_base_url="http://localhost:1234/v1",
        api_key="",
        vlm_model="test-model",
        evaluation_vlm_model="test-model",
        planner_model="test-model",
        max_iterations=10,
        target_style_score=85.0,
        min_strokes_per_layer=MIN_STROKES_PER_LAYER,
    )


def _build_orchestrator(tmp_path: Path) -> GenerationOrchestrator:
    """Create a GenerationOrchestrator pointing at a temp directory."""
    return GenerationOrchestrator(
        artist_name="Test Artist",
        subject="Test Subject",
        artwork_id="test-min-strokes",
        output_dir=tmp_path,
        generation_config=_make_test_config(),
    )


def _run_iteration(
    orchestrator: GenerationOrchestrator,
    layer: PlanLayer,
    iteration: int,
    layer_complete: bool,
) -> bool | None:
    """
    Run one iteration with all VLM and persistence calls mocked.

    Returns the return value from ``_execute_iteration()``.
    """
    stroke_response = _make_stroke_response(layer_complete=layer_complete)
    evaluation = _make_evaluation()
    apply_results = _make_apply_strokes_results()

    with (
        patch.object(
            orchestrator.stroke_vlm,
            "suggest_strokes",
            return_value=stroke_response,
        ),
        patch.object(
            orchestrator.canvas_manager,
            "apply_strokes",
            return_value=apply_results,
        ),
        patch.object(
            orchestrator.eval_vlm,
            "evaluate_style",
            return_value=evaluation,
        ),
        patch.object(orchestrator.persistence, "save_stroke_batch"),
        patch.object(orchestrator.persistence, "save_evaluation"),
        patch.object(
            orchestrator.strategy_manager,
            "get_recent_strategies",
            return_value="",
        ),
        patch.object(orchestrator.strategy_manager, "save_current_strategy_link"),
        # canvas_manager.image.save writes snapshot PNGs — let it work with real temp dir
    ):
        return orchestrator._execute_iteration(iteration=iteration, current_layer=layer)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_layer_not_advanced_below_minimum() -> None:
    """Layer index does not advance when layer_complete arrives before minimum.

    With 2 prior iterations and layer_complete=True, the orchestrator must
    ignore the signal and keep current_layer_index at 0.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        orch = _build_orchestrator(tmp_path)
        plan = _make_plan(num_layers=2)
        orch.painting_plan = plan
        orch.current_layer_index = 0
        # Simulate 2 iterations already completed on layer 1
        orch.layer_iterations = {1: 2}

        _run_iteration(orch, plan["layers"][0], iteration=3, layer_complete=True)

        assert orch.current_layer_index == 0, (
            f"Expected layer_index=0 but got {orch.current_layer_index}; "
            "layer should NOT advance before minimum is met"
        )


def test_layer_advanced_at_minimum() -> None:
    """Layer index advances when layer_complete arrives at exactly the minimum.

    Prior iterations = MIN_STROKES_PER_LAYER - 1; the current iteration brings
    the total to MIN_STROKES_PER_LAYER, which is sufficient to advance.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        orch = _build_orchestrator(tmp_path)
        plan = _make_plan(num_layers=2)
        orch.painting_plan = plan
        orch.current_layer_index = 0
        # prior iterations = MIN - 1; +1 for current = MIN exactly
        orch.layer_iterations = {1: MIN_STROKES_PER_LAYER - 1}

        _run_iteration(
            orch,
            plan["layers"][0],
            iteration=MIN_STROKES_PER_LAYER,
            layer_complete=True,
        )

        assert orch.current_layer_index == 1, (
            f"Expected layer_index=1 but got {orch.current_layer_index}; "
            "layer SHOULD advance once minimum is met"
        )


def test_final_layer_stops_generation_at_minimum() -> None:
    """_execute_iteration returns True when final layer completes at minimum.

    Orchestrator is on the last layer (index 1 of 2), layer_iterations has
    MIN_STROKES_PER_LAYER - 1 prior iterations. The current iteration takes
    it to the minimum and layer_complete=True is signalled, so generation ends.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        orch = _build_orchestrator(tmp_path)
        plan = _make_plan(num_layers=2)
        orch.painting_plan = plan
        orch.current_layer_index = 1  # already on final layer
        orch.layer_iterations = {2: MIN_STROKES_PER_LAYER - 1}

        result = _run_iteration(
            orch,
            plan["layers"][1],
            iteration=MIN_STROKES_PER_LAYER,
            layer_complete=True,
        )

        assert result is True, (
            f"Expected True (stop generation) but got {result!r}; "
            "final layer at minimum should end generation"
        )


def test_final_layer_does_not_stop_below_minimum() -> None:
    """_execute_iteration does NOT return True when final layer is below minimum.

    Even with layer_complete=True, if the minimum hasn't been reached the
    final-layer stop block must be skipped and normal logic continues.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        orch = _build_orchestrator(tmp_path)
        plan = _make_plan(num_layers=2)
        orch.painting_plan = plan
        orch.current_layer_index = 1  # on final layer
        orch.layer_iterations = {2: 2}  # only 2 prior iterations, well below minimum

        result = _run_iteration(
            orch,
            plan["layers"][1],
            iteration=3,
            layer_complete=True,
        )

        # Score=50, iteration=3 — well inside min/max stopping bounds,
        # so _check_stopping_conditions also returns False.
        # The final-layer guard must not fire here either.
        assert result is not True, (
            "Final-layer stop should not fire when below minimum — "
            f"layer_iterations={orch.layer_iterations}, MIN={MIN_STROKES_PER_LAYER}"
        )
