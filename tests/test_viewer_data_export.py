"""Unit tests for viewer data export (Phase 6).

Tests the ``_save_viewer_data()`` method on ``GenerationOrchestrator`` and
verifies that the enriched ``viewer_data.json`` has the expected schema,
stroke count, enrichment fields, metadata, and that the viewer HTML
template is copied into the output directory.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import (
    CANVAS_BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    NEXTJS_VIEWER_DATA_DIR,
    OUTPUT_STRUCTURE,
    VIEWER_DATA_FILENAME,
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
def orchestrator_with_batches() -> Generator[
    tuple[GenerationOrchestrator, Path], None, None
]:
    """Create an orchestrator with pre-populated batch files and evaluations.

    Returns:
        Generator[tuple[GenerationOrchestrator, Path], None, None]: The orchestrator and its temp directory
    """
    tmpdir = Path(tempfile.mkdtemp())
    orch = GenerationOrchestrator(
        artist_name="Test Artist",
        subject="Test Subject",
        artwork_id="test-viewer-001",
        output_dir=tmpdir,
        generation_config=_make_test_config(),
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
        {
            "score": 35.0,
            "feedback": "ok",
            "strengths": "",
            "suggestions": "",
            "timestamp": "2026-01-01T00:00:00",
            "iteration": 1,
        },
        {
            "score": 55.0,
            "feedback": "better",
            "strengths": "",
            "suggestions": "",
            "timestamp": "2026-01-01T00:01:00",
            "iteration": 2,
        },
    ]

    yield orch, tmpdir

    # Cleanup: Remove test data from Next.js public directory
    import shutil

    nextjs_test_data = NEXTJS_VIEWER_DATA_DIR / orch.artwork_id
    if nextjs_test_data.exists():
        shutil.rmtree(nextjs_test_data)


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
    """Test that viewer data is written to both local and Next.js directories."""

    def test_viewer_data_exists_locally(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """viewer_data.json should be present in the local viewer output directory."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        data_path = viewer_dir / VIEWER_DATA_FILENAME
        assert data_path.exists(), (
            "viewer_data.json was not created in local viewer directory"
        )

    def test_viewer_data_is_valid_json_locally(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Local viewer_data.json should be valid JSON."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        data_path = viewer_dir / VIEWER_DATA_FILENAME
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)  # Should not raise
        assert isinstance(data, dict)


class TestViewerDataWrittenToNextJsDir:
    """Test that viewer data is written to the Next.js public/data directory."""

    def test_nextjs_viewer_data_exists(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """viewer_data.json should be present in Next.js public/data/<artwork_id>/ directory."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        nextjs_data_path = (
            NEXTJS_VIEWER_DATA_DIR / orch.artwork_id / VIEWER_DATA_FILENAME
        )
        assert nextjs_data_path.exists(), (
            f"viewer_data.json was not created in Next.js data directory at {nextjs_data_path}"
        )

    def test_nextjs_viewer_data_is_valid_json(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Next.js viewer_data.json should be valid JSON."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        nextjs_data_path = (
            NEXTJS_VIEWER_DATA_DIR / orch.artwork_id / VIEWER_DATA_FILENAME
        )
        with open(nextjs_data_path, encoding="utf-8") as f:
            data = json.load(f)  # Should not raise
        assert isinstance(data, dict)

    def test_nextjs_viewer_data_matches_local(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Next.js viewer_data.json should match the local copy."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        local_viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        local_data_path = local_viewer_dir / VIEWER_DATA_FILENAME
        with open(local_data_path, encoding="utf-8") as f:
            local_data = json.load(f)

        nextjs_data_path = (
            NEXTJS_VIEWER_DATA_DIR / orch.artwork_id / VIEWER_DATA_FILENAME
        )
        with open(nextjs_data_path, encoding="utf-8") as f:
            nextjs_data = json.load(f)

        assert local_data == nextjs_data, (
            "Local and Next.js viewer data should be identical"
        )

    def test_nextjs_metadata_artwork_id_matches(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Next.js viewer_data.json metadata.artwork_id should match the orchestrator's artwork_id."""
        orch, _ = orchestrator_with_batches
        orch._save_viewer_data()

        nextjs_data_path = (
            NEXTJS_VIEWER_DATA_DIR / orch.artwork_id / VIEWER_DATA_FILENAME
        )
        with open(nextjs_data_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["metadata"]["artwork_id"] == orch.artwork_id


class TestViewerThumbnailGenerated:
    """Test that thumbnail is generated and saved to Next.js public/data directory."""

    def test_thumbnail_created(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Thumbnail should be created when final artwork exists."""
        orch, _ = orchestrator_with_batches

        # Create a mock final_artwork.png
        from PIL import Image

        final_artwork_path = (
            orch.artwork_dir / f"{OUTPUT_STRUCTURE['final_artwork']}.png"
        )
        img = Image.new("RGB", (800, 600), color="white")
        img.save(final_artwork_path, "PNG")

        # Call _save_viewer_data which should trigger thumbnail generation
        orch._save_viewer_data()

        thumbnail_path = NEXTJS_VIEWER_DATA_DIR / orch.artwork_id / "thumbnail.png"
        assert thumbnail_path.exists(), f"Thumbnail was not created at {thumbnail_path}"

    def test_thumbnail_is_valid_png(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Thumbnail should be a valid PNG image."""
        orch, _ = orchestrator_with_batches

        # Create a mock final_artwork.png
        from PIL import Image

        final_artwork_path = (
            orch.artwork_dir / f"{OUTPUT_STRUCTURE['final_artwork']}.png"
        )
        img = Image.new("RGB", (800, 600), color="white")
        img.save(final_artwork_path, "PNG")

        orch._save_viewer_data()

        thumbnail_path = NEXTJS_VIEWER_DATA_DIR / orch.artwork_id / "thumbnail.png"
        # Try to open the thumbnail - should not raise
        thumb_img = Image.open(thumbnail_path)
        assert thumb_img.format == "PNG"

    def test_thumbnail_dimensions(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Thumbnail dimensions should be ≤ 400×400 pixels."""
        orch, _ = orchestrator_with_batches

        # Create a mock final_artwork.png larger than 400x400
        from PIL import Image

        final_artwork_path = (
            orch.artwork_dir / f"{OUTPUT_STRUCTURE['final_artwork']}.png"
        )
        img = Image.new("RGB", (800, 600), color="white")
        img.save(final_artwork_path, "PNG")

        orch._save_viewer_data()

        thumbnail_path = NEXTJS_VIEWER_DATA_DIR / orch.artwork_id / "thumbnail.png"
        thumb_img = Image.open(thumbnail_path)
        width, height = thumb_img.size

        assert width <= 400, f"Thumbnail width {width} exceeds 400px"
        assert height <= 400, f"Thumbnail height {height} exceeds 400px"

    def test_thumbnail_not_created_without_final_artwork(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
    ) -> None:
        """Thumbnail should not be created if final artwork doesn't exist."""
        orch, _ = orchestrator_with_batches

        # Don't create final_artwork.png
        orch._save_viewer_data()

        thumbnail_path = NEXTJS_VIEWER_DATA_DIR / orch.artwork_id / "thumbnail.png"
        assert not thumbnail_path.exists(), (
            "Thumbnail should not be created without final artwork"
        )


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
        nextjs_test_dir = NEXTJS_VIEWER_DATA_DIR / "test-skip-001"

        try:
            orch = GenerationOrchestrator(
                artist_name="Skip Test",
                subject="Skip Subject",
                artwork_id="test-skip-001",
                output_dir=tmpdir,
                generation_config=_make_test_config(),
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
            with open(
                strokes_dir / "iteration-001_batch.json", "w", encoding="utf-8"
            ) as f:
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

        finally:
            # Cleanup: Remove the test directory from Next.js viewer data
            if nextjs_test_dir.exists():
                shutil.rmtree(nextjs_test_dir)


class TestViewerDataEvaluations:
    """Test that evaluations array is included in viewer data output."""

    def test_evaluations_key_exists(self, viewer_data: dict[str, Any]) -> None:
        """Viewer data must contain an 'evaluations' key."""
        assert "evaluations" in viewer_data

    def test_evaluations_is_list(self, viewer_data: dict[str, Any]) -> None:
        """The 'evaluations' value must be a list."""
        assert isinstance(viewer_data["evaluations"], list)

    def test_evaluations_count_matches_orchestrator(
        self,
        orchestrator_with_batches: tuple[GenerationOrchestrator, Path],
        viewer_data: dict[str, Any],
    ) -> None:
        """Evaluation count must match the number of evaluations on the orchestrator."""
        orch, _ = orchestrator_with_batches
        assert len(viewer_data["evaluations"]) == len(orch.evaluations)

    def test_each_evaluation_has_required_fields(
        self, viewer_data: dict[str, Any]
    ) -> None:
        """Each evaluation object must have iteration, score, feedback, strengths, suggestions."""
        required_fields = ["iteration", "score", "feedback", "strengths", "suggestions"]
        for i, ev in enumerate(viewer_data["evaluations"]):
            for field in required_fields:
                assert field in ev, f"Evaluation {i} missing field '{field}'"

    def test_evaluation_scores_match_source(self, viewer_data: dict[str, Any]) -> None:
        """Evaluation scores in the array should match the fixture values."""
        scores = [ev["score"] for ev in viewer_data["evaluations"]]
        assert scores == [35.0, 55.0]

    def test_evaluation_iterations_match_source(
        self, viewer_data: dict[str, Any]
    ) -> None:
        """Evaluation iteration values should match the fixture values."""
        iterations = [ev["iteration"] for ev in viewer_data["evaluations"]]
        assert iterations == [1, 2]

    def test_evaluation_feedback_values(self, viewer_data: dict[str, Any]) -> None:
        """Evaluation feedback strings should match the fixture values."""
        feedbacks = [ev["feedback"] for ev in viewer_data["evaluations"]]
        assert feedbacks == ["ok", "better"]

    def test_evaluations_empty_when_no_evaluations(self) -> None:
        """Evaluations array should be empty when orchestrator has no evaluations."""
        tmpdir = Path(tempfile.mkdtemp())
        nextjs_test_dir = NEXTJS_VIEWER_DATA_DIR / "test-no-evals-001"

        try:
            orch = GenerationOrchestrator(
                artist_name="No Eval Artist",
                subject="No Eval Subject",
                artwork_id="test-no-evals-001",
                output_dir=tmpdir,
                generation_config=_make_test_config(),
            )

            strokes_dir = orch.artwork_dir / OUTPUT_STRUCTURE["strokes"]
            strokes_dir.mkdir(parents=True, exist_ok=True)

            _make_batch_file(
                strokes_dir,
                iteration=1,
                strokes=[_sample_line_stroke()],
            )

            orch.evaluations = []
            orch._save_viewer_data()

            viewer_dir = orch.artwork_dir / OUTPUT_STRUCTURE["viewer"]
            data_path = viewer_dir / VIEWER_DATA_FILENAME
            with open(data_path, encoding="utf-8") as f:
                data = json.load(f)

            assert data["evaluations"] == []

        finally:
            if nextjs_test_dir.exists():
                shutil.rmtree(nextjs_test_dir)


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
