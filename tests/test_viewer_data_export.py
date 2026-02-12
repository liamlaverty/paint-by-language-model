"""Unit tests for viewer data export (Phase 6).

Tests the ``_save_viewer_data()`` method on ``GenerationOrchestrator`` and
verifies that the enriched ``viewer_data.json`` has the expected schema,
stroke count, enrichment fields, metadata, and that the viewer HTML
template is copied into the output directory.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import (
    CANVAS_BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    OUTPUT_STRUCTURE,
    VIEWER_DATA_FILENAME,
)
from generation_orchestrator import GenerationOrchestrator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_batch_file(
    strokes_dir: Path,
    iteration: int,
    strokes: list[dict[str, Any]],
    reasoning: str = "Test reasoning",
) -> None:
    """Create a batch file matching the generation pipeline format.

    Args:
        strokes_dir (Path): Directory to write the batch file into
        iteration (int): Iteration number (used in filename and content)
        strokes (list[dict[str, Any]]): Stroke dicts for the batch
        reasoning (str): Batch reasoning text
    """
    batch: dict[str, Any] = {
        "iteration": iteration,
        "batch_reasoning": reasoning,
        "strokes": strokes,
        "applied_count": len(strokes),
        "skipped_count": 0,
        "total_requested": len(strokes),
        "timestamp": "2026-01-01T00:00:00",
        "results": [{"success": True, "stroke_index": i} for i in range(len(strokes))],
    }
    filename = f"iteration-{iteration:03d}_batch.json"
    with open(strokes_dir / filename, "w", encoding="utf-8") as f:
        json.dump(batch, f)


def _sample_line_stroke() -> dict[str, Any]:
    """Return a minimal line stroke dict."""
    return {
        "type": "line",
        "color_hex": "#FF0000",
        "thickness": 3,
        "opacity": 0.9,
        "start_x": 10,
        "start_y": 20,
        "end_x": 100,
        "end_y": 200,
    }


def _sample_arc_stroke() -> dict[str, Any]:
    """Return a minimal arc stroke dict."""
    return {
        "type": "arc",
        "color_hex": "#00FF00",
        "thickness": 2,
        "opacity": 0.7,
        "arc_bbox": [50, 50, 200, 150],
        "arc_start_angle": 0,
        "arc_end_angle": 180,
    }


def _sample_polyline_stroke() -> dict[str, Any]:
    """Return a minimal polyline stroke dict."""
    return {
        "type": "polyline",
        "color_hex": "#0000FF",
        "thickness": 4,
        "opacity": 0.8,
        "points": [[10, 10], [50, 50], [90, 30], [120, 80]],
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def orchestrator_with_batches() -> tuple[GenerationOrchestrator, Path]:
    """Create an orchestrator with pre-populated batch files and evaluations.

    Returns:
        tuple[GenerationOrchestrator, Path]: The orchestrator and its temp directory
    """
    tmpdir = Path(tempfile.mkdtemp())
    orch = GenerationOrchestrator(
        artist_name="Test Artist",
        subject="Test Subject",
        artwork_id="test-viewer-001",
        output_dir=tmpdir,
    )

    # Create batch files in the strokes sub-directory
    strokes_dir = orch.artwork_dir / OUTPUT_STRUCTURE["strokes"]
    strokes_dir.mkdir(parents=True, exist_ok=True)

    # Iteration 1: 2 strokes
    _make_batch_file(
        strokes_dir,
        iteration=1,
        strokes=[_sample_line_stroke(), _sample_arc_stroke()],
        reasoning="First batch: lay down foundational lines",
    )
    # Iteration 2: 1 stroke
    _make_batch_file(
        strokes_dir,
        iteration=2,
        strokes=[_sample_polyline_stroke()],
        reasoning="Second batch: add polyline detail",
    )

    # Populate evaluations so score_progression is non-empty
    orch.evaluations = [
        {"score": 35.0, "feedback": "ok", "strengths": [], "suggestions": []},
        {"score": 55.0, "feedback": "better", "strengths": [], "suggestions": []},
    ]

    return orch, tmpdir


@pytest.fixture
def viewer_data(
    orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
) -> dict[str, Any]:
    """Run ``_save_viewer_data()`` and return the parsed JSON.

    Args:
        orchestrator_with_batches (tuple): Fixture providing orchestrator and tmpdir

    Returns:
        dict[str, Any]: Parsed viewer_data.json contents
    """
    orch, _ = orchestrator_with_batches
    orch._save_viewer_data()

    viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
    data_path = viewer_dir / VIEWER_DATA_FILENAME
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestViewerDataStructure:
    """Test that the viewer data JSON has the correct top-level schema."""

    def test_has_metadata_key(self, viewer_data: dict[str, Any]) -> None:
        """Viewer data must contain a 'metadata' key."""
        assert "metadata" in viewer_data

    def test_has_strokes_key(self, viewer_data: dict[str, Any]) -> None:
        """Viewer data must contain a 'strokes' key."""
        assert "strokes" in viewer_data

    def test_strokes_is_list(self, viewer_data: dict[str, Any]) -> None:
        """The 'strokes' value must be a list."""
        assert isinstance(viewer_data["strokes"], list)

    def test_metadata_is_dict(self, viewer_data: dict[str, Any]) -> None:
        """The 'metadata' value must be a dict."""
        assert isinstance(viewer_data["metadata"], dict)


class TestViewerDataStrokeCount:
    """Test that the stroke count is consistent with the batch files."""

    def test_stroke_count_matches_batches(self, viewer_data: dict[str, Any]) -> None:
        """Total strokes should equal the sum of successful strokes across batches."""
        # We created 2 strokes in batch 1 + 1 stroke in batch 2 = 3
        assert len(viewer_data["strokes"]) == 3

    def test_metadata_total_strokes_matches(self, viewer_data: dict[str, Any]) -> None:
        """metadata.total_strokes should match the actual strokes array length."""
        assert viewer_data["metadata"]["total_strokes"] == len(viewer_data["strokes"])


class TestViewerDataEnrichmentFields:
    """Test that each stroke has the required enrichment fields."""

    ENRICHMENT_FIELDS = ["index", "iteration", "batch_position", "batch_reasoning"]

    def test_all_strokes_have_enrichment_fields(
        self, viewer_data: dict[str, Any]
    ) -> None:
        """Every stroke must have index, iteration, batch_position, batch_reasoning."""
        for stroke in viewer_data["strokes"]:
            for field in self.ENRICHMENT_FIELDS:
                assert field in stroke, (
                    f"Stroke {stroke.get('index', '?')} missing '{field}'"
                )

    def test_index_is_sequential(self, viewer_data: dict[str, Any]) -> None:
        """Stroke indices must be sequential starting from 0."""
        indices = [s["index"] for s in viewer_data["strokes"]]
        assert indices == list(range(len(indices)))

    def test_iteration_values_match_batches(self, viewer_data: dict[str, Any]) -> None:
        """Iteration numbers should come from the batch files we created."""
        iterations = [s["iteration"] for s in viewer_data["strokes"]]
        # Batch 1 had 2 strokes (iter 1), batch 2 had 1 stroke (iter 2)
        assert iterations == [1, 1, 2]

    def test_batch_position_resets_per_batch(self, viewer_data: dict[str, Any]) -> None:
        """Batch position should reset for each iteration batch."""
        positions = [s["batch_position"] for s in viewer_data["strokes"]]
        # Batch 1: positions 0, 1; Batch 2: position 0
        assert positions == [0, 1, 0]

    def test_batch_reasoning_is_nonempty(self, viewer_data: dict[str, Any]) -> None:
        """Batch reasoning should be populated from the batch file."""
        for stroke in viewer_data["strokes"]:
            assert len(stroke["batch_reasoning"]) > 0

    def test_original_stroke_fields_preserved(
        self, viewer_data: dict[str, Any]
    ) -> None:
        """The original stroke rendering fields (type, color_hex, etc.) must survive enrichment."""
        required_render_fields = ["type", "color_hex", "thickness", "opacity"]
        for stroke in viewer_data["strokes"]:
            for field in required_render_fields:
                assert field in stroke, (
                    f"Stroke {stroke['index']} missing render field '{field}'"
                )


class TestViewerDataMetadataFields:
    """Test that the metadata section has all expected fields."""

    REQUIRED_METADATA = [
        "artwork_id",
        "artist_name",
        "subject",
        "canvas_width",
        "canvas_height",
        "background_color",
        "total_strokes",
        "total_iterations",
        "score_progression",
    ]

    def test_all_required_metadata_present(self, viewer_data: dict[str, Any]) -> None:
        """Metadata must contain all required fields."""
        for field in self.REQUIRED_METADATA:
            assert field in viewer_data["metadata"], f"Metadata missing '{field}'"

    def test_canvas_dimensions(self, viewer_data: dict[str, Any]) -> None:
        """Canvas dimensions should match config constants."""
        meta = viewer_data["metadata"]
        assert meta["canvas_width"] == CANVAS_WIDTH
        assert meta["canvas_height"] == CANVAS_HEIGHT

    def test_background_color(self, viewer_data: dict[str, Any]) -> None:
        """Background color should match config constant."""
        assert viewer_data["metadata"]["background_color"] == CANVAS_BACKGROUND_COLOR

    def test_artwork_id(self, viewer_data: dict[str, Any]) -> None:
        """Artwork ID should match what the orchestrator was initialized with."""
        assert viewer_data["metadata"]["artwork_id"] == "test-viewer-001"

    def test_artist_name(self, viewer_data: dict[str, Any]) -> None:
        """Artist name should match the orchestrator's artist_name."""
        assert viewer_data["metadata"]["artist_name"] == "Test Artist"

    def test_subject(self, viewer_data: dict[str, Any]) -> None:
        """Subject should match the orchestrator's subject."""
        assert viewer_data["metadata"]["subject"] == "Test Subject"

    def test_total_iterations(self, viewer_data: dict[str, Any]) -> None:
        """Total iterations should equal the number of batch files."""
        assert viewer_data["metadata"]["total_iterations"] == 2

    def test_score_progression(self, viewer_data: dict[str, Any]) -> None:
        """Score progression should contain the evaluation scores we set."""
        assert viewer_data["metadata"]["score_progression"] == [35.0, 55.0]


class TestViewerHtmlCopied:
    """Test that the viewer HTML template is copied to the output directory."""

    def test_viewer_html_exists(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """index.html should be present in the viewer output directory after save."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        html_path = viewer_dir / "index.html"
        assert html_path.exists(), "viewer index.html was not copied to output"

    def test_viewer_html_is_nonempty(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Copied index.html should have content (not an empty file)."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        html_path = viewer_dir / "index.html"
        assert html_path.stat().st_size > 0, "viewer index.html is empty"

    def test_viewer_html_contains_canvas(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Copied index.html should contain a canvas element."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        html_path = viewer_dir / "index.html"
        content = html_path.read_text(encoding="utf-8")
        assert "<canvas" in content, "viewer index.html does not contain <canvas>"


class TestViewerDataIterationNumbers:
    """Test that iteration numbers are sequential and match batch files."""

    def test_iteration_numbers_are_sequential(
        self, viewer_data: dict[str, Any]
    ) -> None:
        """Unique iteration numbers should form a sequential 1-based range."""
        iterations = sorted(set(s["iteration"] for s in viewer_data["strokes"]))
        expected = list(range(1, len(iterations) + 1))
        assert iterations == expected

    def test_iteration_count_matches_metadata(
        self, viewer_data: dict[str, Any]
    ) -> None:
        """Number of unique iterations should equal metadata.total_iterations."""
        unique_iters = set(s["iteration"] for s in viewer_data["strokes"])
        assert len(unique_iters) == viewer_data["metadata"]["total_iterations"]


class TestViewerDataSkippedStrokes:
    """Test that strokes marked as failed in batch results are excluded."""

    def test_skipped_strokes_not_in_output(self) -> None:
        """Strokes with success=False should be omitted from viewer data."""
        tmpdir = Path(tempfile.mkdtemp())
        orch = GenerationOrchestrator(
            artist_name="Skip Test",
            subject="Skip Subject",
            artwork_id="test-skip-001",
            output_dir=tmpdir,
        )

        strokes_dir = orch.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        strokes_dir.mkdir(parents=True, exist_ok=True)

        # Create a batch where one stroke succeeded and one failed
        batch: dict[str, Any] = {
            "iteration": 1,
            "batch_reasoning": "Mixed results",
            "strokes": [_sample_line_stroke(), _sample_arc_stroke()],
            "applied_count": 1,
            "skipped_count": 1,
            "total_requested": 2,
            "timestamp": "2026-01-01T00:00:00",
            "results": [
                {"success": True, "stroke_index": 0},
                {"success": False, "stroke_index": 1, "error": "Out of bounds"},
            ],
        }
        with open(strokes_dir / "iteration-001_batch.json", "w", encoding="utf-8") as f:
            json.dump(batch, f)

        orch.evaluations = []
        orch._save_viewer_data()

        viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        data_path = viewer_dir / VIEWER_DATA_FILENAME
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        # Only the successful stroke should appear
        assert len(data["strokes"]) == 1
        assert data["strokes"][0]["type"] == "line"
        assert data["metadata"]["total_strokes"] == 1


class TestViewerDataJsonFile:
    """Test the viewer_data.json file itself is valid and well-formed."""

    def test_viewer_data_file_exists(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """viewer_data.json should be created in the viewer directory."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        data_path = viewer_dir / VIEWER_DATA_FILENAME
        assert data_path.exists()

    def test_viewer_data_is_valid_json(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """viewer_data.json should be parseable JSON."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        data_path = viewer_dir / VIEWER_DATA_FILENAME
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)  # Should not raise
        assert isinstance(data, dict)
