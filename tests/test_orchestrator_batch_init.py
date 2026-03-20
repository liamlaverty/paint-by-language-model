"""Test for orchestrator batch mode initialization."""

import sys
import tempfile
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import DEFAULT_STROKES_PER_QUERY
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


def test_orchestrator_batch_initialization() -> None:
    """Test that orchestrator initializes correctly with batch parameters."""
    # Create test instance with custom strokes_per_query
    test_dir = Path(tempfile.mkdtemp())
    orchestrator = GenerationOrchestrator(
        artist_name="Test Artist",
        subject="Test Subject",
        artwork_id="test-001",
        output_dir=test_dir,
        strokes_per_query=3,  # Custom value
        generation_config=_make_test_config(),
    )

    # Verify basic attributes
    assert orchestrator.artist_name == "Test Artist"
    assert orchestrator.subject == "Test Subject"
    assert orchestrator.strokes_per_query == 3

    # Verify batch tracking fields exist and are initialized
    assert orchestrator.total_strokes_requested == 0
    assert orchestrator.total_strokes_applied == 0
    assert orchestrator.total_strokes_skipped == 0
    assert orchestrator.stroke_type_counts == {}

    print("✓ Orchestrator batch initialization test passed")
    print(f"  Artist: {orchestrator.artist_name}")
    print(f"  Subject: {orchestrator.subject}")
    print(f"  Strokes per query: {orchestrator.strokes_per_query}")
    print("  Batch tracking fields initialized correctly")


def test_orchestrator_default_strokes_per_query() -> None:
    """Test that orchestrator uses default strokes_per_query when not specified."""
    test_dir = Path(tempfile.mkdtemp())

    # Create instance without specifying strokes_per_query
    orchestrator = GenerationOrchestrator(
        artist_name="Test Artist",
        subject="Test Subject",
        artwork_id="test-002",
        output_dir=test_dir,
        generation_config=_make_test_config(),
        # strokes_per_query not specified - should use default
    )

    # Verify it uses the default value from config
    assert orchestrator.strokes_per_query == DEFAULT_STROKES_PER_QUERY

    print("✓ Default strokes_per_query test passed")
    print(f"  Expected: {DEFAULT_STROKES_PER_QUERY}")
    print(f"  Actual: {orchestrator.strokes_per_query}")


if __name__ == "__main__":
    test_orchestrator_batch_initialization()
    test_orchestrator_default_strokes_per_query()
