"""Integration test for Generation Orchestrator."""

import tempfile
from pathlib import Path

from paint_by_language_model.generation_orchestrator import GenerationOrchestrator

# Create test output directory
test_dir = Path(tempfile.mkdtemp())

try:
    # Initialize orchestrator
    orchestrator = GenerationOrchestrator(
        artist_name="Vincent van Gogh",
        subject="Simple Landscape",
        artwork_id="test-integration-001",
        output_dir=test_dir,
    )

    print("Starting generation (will run a few iterations)...")
    print("Press Ctrl+C to interrupt early")

    # Run generation
    summary = orchestrator.generate()

    print("\n" + "=" * 80)
    print("Generation Complete!")
    print("=" * 80)
    print(f"Artwork ID: {summary['artwork_id']}")
    print(f"Total Iterations: {summary['total_iterations']}")
    print(f"Final Score: {summary['final_score']:.1f}/100")
    print(f"Total Strokes: {summary['total_strokes']}")
    print(f"Output: {summary['output_directory']}")
    print("=" * 80)

    # Verify artifacts exist
    artwork_dir = Path(summary["output_directory"])
    assert (artwork_dir / "final_artwork.png").exists(), "Final artwork missing"
    assert (artwork_dir / "metadata.json").exists(), "Metadata missing"
    assert (artwork_dir / "generation_report.md").exists(), "Report missing"
    assert (artwork_dir / "snapshots").exists(), "Snapshots directory missing"

    print("\n✓ All artifacts generated successfully!")

except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback

    traceback.print_exc()
finally:
    # Cleanup (comment out to inspect output)
    # shutil.rmtree(test_dir)
    print(f"\nTest output saved to: {test_dir}")
