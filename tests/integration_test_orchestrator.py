"""Integration test for Generation Orchestrator."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Pytest tests
# ---------------------------------------------------------------------------


def _make_plan_json(stroke_types: list[str] | None = None) -> str:
    """Return a minimal PaintingPlan JSON string."""
    return json.dumps(
        {
            "artist_name": "Test Artist",
            "subject": "Test Subject",
            "expanded_subject": None,
            "total_layers": 1,
            "overall_notes": "Test",
            "layers": [
                {
                    "layer_number": 1,
                    "name": "Background",
                    "description": "Background layer",
                    "colour_palette": ["#FFFFFF"],
                    "stroke_types": stroke_types or ["line"],
                    "techniques": "broad",
                    "shapes": "rectangles",
                    "highlights": "none",
                }
            ],
        }
    )


def test_orchestrator_passes_allowed_stroke_types_to_planner() -> None:
    """GenerationOrchestrator passes allowed_stroke_types to planner.generate_plan.

    When constructed with ``allowed_stroke_types=["line", "circle"]``, the
    orchestrator must call ``planner.generate_plan`` with ``["line", "circle"]``
    and NOT with the module-level ``SUPPORTED_STROKE_TYPES`` constant.
    """
    import sys

    sys.path.insert(
        0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
    )

    from generation_orchestrator import GenerationOrchestrator
    from models import GenerationConfig

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
            min_strokes_per_layer=1,
        )

    allowed = ["line", "circle"]
    test_dir = Path(tempfile.mkdtemp())

    mock_plan_json = _make_plan_json(stroke_types=allowed)

    # Patch PlannerLLMClient so no real VLM call happens and capture the call args
    with patch("generation_orchestrator.PlannerLLMClient") as MockPlanner:
        mock_planner_instance = MagicMock()
        mock_planner_instance.generate_plan.return_value = json.loads(mock_plan_json)
        MockPlanner.return_value = mock_planner_instance

        # Also patch StrokeVLMClient and EvaluationVLMClient to prevent real VLM calls
        with (
            patch("generation_orchestrator.StrokeVLMClient"),
            patch("generation_orchestrator.EvaluationVLMClient"),
        ):
            orchestrator = GenerationOrchestrator(
                artist_name="Test Artist",
                subject="Test Subject",
                artwork_id="test-allowed-types-001",
                output_dir=test_dir,
                allowed_stroke_types=allowed,
                generation_config=_make_test_config(),
            )

            # Call _run_planning_phase directly (avoids running full generation loop)
            orchestrator._run_planning_phase()

    # Verify generate_plan was called with the effective allowed list, not SUPPORTED_STROKE_TYPES
    mock_planner_instance.generate_plan.assert_called_once()
    call_args = mock_planner_instance.generate_plan.call_args
    # stroke_types is the 4th positional arg (index 3) or keyword
    stroke_types_used: list[str] = call_args.kwargs.get("stroke_types") or (
        call_args.args[3] if len(call_args.args) > 3 else None
    )
    assert stroke_types_used == allowed, (
        f"Expected generate_plan called with {allowed}, got {stroke_types_used}"
    )


# ---------------------------------------------------------------------------
# Standalone script (not collected by pytest)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from paint_by_language_model.generation_orchestrator import GenerationOrchestrator

    # Create test output directory
    _test_dir = Path(tempfile.mkdtemp())

    try:
        # Initialize orchestrator
        _orchestrator = GenerationOrchestrator(
            artist_name="Vincent van Gogh",
            subject="Simple Landscape",
            artwork_id="test-integration-001",
            output_dir=_test_dir,
        )

        print("Starting generation (will run a few iterations)...")
        print("Press Ctrl+C to interrupt early")

        # Run generation
        _summary = _orchestrator.generate()

        print("\n" + "=" * 80)
        print("Generation Complete!")
        print("=" * 80)
        print(f"Artwork ID: {_summary['artwork_id']}")
        print(f"Total Iterations: {_summary['total_iterations']}")
        print(f"Final Score: {_summary['final_score']:.1f}/100")
        print(f"Total Strokes: {_summary['total_strokes']}")
        print(f"Output: {_summary['output_directory']}")
        print("=" * 80)

        # Verify artifacts exist
        _artwork_dir = Path(_summary["output_directory"])
        assert (_artwork_dir / "final_artwork.png").exists(), "Final artwork missing"
        assert (_artwork_dir / "metadata.json").exists(), "Metadata missing"
        assert (_artwork_dir / "generation_report.md").exists(), "Report missing"
        assert (_artwork_dir / "snapshots").exists(), "Snapshots directory missing"

        print("\n✓ All artifacts generated successfully!")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as _e:
        print(f"\n✗ Test failed: {_e}")
        import traceback

        traceback.print_exc()
    finally:
        # Cleanup (comment out to inspect output)
        # shutil.rmtree(_test_dir)
        print(f"\nTest output saved to: {_test_dir}")
