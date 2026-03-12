"""Unit tests for ArtworkStateLoader service."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.state_loader import ArtworkStateLoader

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_canvas_manager_mock() -> MagicMock:
    """Return a MagicMock standing in for CanvasManager.

    Returns:
        MagicMock: Mock canvas manager with apply_stroke wired up.
    """
    mock = MagicMock()
    mock.apply_stroke = MagicMock()
    return mock


def _write_batch_file(
    strokes_dir: Path,
    iteration: int,
    strokes: list,
    applied: bool = True,
    layer_number: int | None = None,
) -> None:
    """Write a minimal batch JSON file to *strokes_dir*.

    Args:
        strokes_dir (Path): Directory in which to write the file.
        iteration (int): Iteration number used for both the filename and
            the ``iteration`` key inside the JSON.
        strokes (list): List of stroke dicts to embed.
        applied (bool): Whether each stroke result should be marked as
            successful (``True``) or failed (``False``).
        layer_number (int | None): Layer number to embed, or ``None``.
    """
    results = [
        {
            "stroke_index": i,
            "stroke_type": s["type"],
            "success": applied,
            "error": None if applied else "test error",
        }
        for i, s in enumerate(strokes)
    ]

    batch = {
        "iteration": iteration,
        "strokes": strokes,
        "batch_reasoning": f"Batch {iteration}",
        "applied_count": len(strokes) if applied else 0,
        "skipped_count": 0 if applied else len(strokes),
        "total_requested": len(strokes),
        "timestamp": "2026-01-01T00:00:00",
        "layer_number": layer_number,
        "layer_name": None,
        "layer_complete": None,
        "results": results,
    }

    filename = f"iteration-{iteration:03d}_batch.json"
    with open(strokes_dir / filename, "w", encoding="utf-8") as f:
        json.dump(batch, f)


def _make_stroke(stroke_type: str = "line") -> dict:
    """Build a minimal stroke dict.

    Args:
        stroke_type (str): The stroke type string.

    Returns:
        dict: A minimal stroke-compatible dict.
    """
    return {
        "type": stroke_type,
        "x1": 0,
        "y1": 0,
        "x2": 50,
        "y2": 50,
        "color": "#000000",
        "thickness": 2,
        "opacity": 1.0,
        "reasoning": "test",
    }


def _write_legacy_stroke_file(strokes_dir: Path, iteration: int, stroke: dict) -> None:
    """Write a single-stroke legacy JSON file.

    Args:
        strokes_dir (Path): Directory in which to write the file.
        iteration (int): Iteration number for the filename.
        stroke (dict): The stroke dict to serialise.
    """
    filename = f"iteration-{iteration:03d}.json"
    with open(strokes_dir / filename, "w", encoding="utf-8") as f:
        json.dump(stroke, f)


def _write_evaluation_file(eval_dir: Path, iteration: int) -> None:
    """Write a minimal evaluation JSON file.

    Args:
        eval_dir (Path): Directory in which to write the file.
        iteration (int): Iteration number for both the filename and the
            ``iteration`` key inside the JSON.
    """
    record = {
        "iteration": iteration,
        "score": 55.0,
        "feedback": "ok",
        "strengths": "nice",
        "suggestions": "more",
        "weaknesses": "none",
    }
    filename = f"iteration-{iteration:03d}.json"
    with open(eval_dir / filename, "w", encoding="utf-8") as f:
        json.dump(record, f)


def _setup_dirs(artwork_dir: Path) -> tuple[Path, Path]:
    """Create the strokes/ and evaluations/ subdirectories.

    Args:
        artwork_dir (Path): Root artwork directory.

    Returns:
        tuple[Path, Path]: ``(strokes_dir, eval_dir)``
    """
    strokes_dir = artwork_dir / "strokes"
    eval_dir = artwork_dir / "evaluations"
    strokes_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)
    return strokes_dir, eval_dir


# ---------------------------------------------------------------------------
# Fresh state (no existing files)
# ---------------------------------------------------------------------------


class TestFreshState:
    """Tests for ArtworkStateLoader when no persisted state exists."""

    def test_returns_starting_iteration_one(self, tmp_path: Path) -> None:
        """When no files exist, starting_iteration must be 1."""
        artwork_dir = tmp_path / "artwork-001"
        artwork_dir.mkdir()
        loader = ArtworkStateLoader(artwork_dir=artwork_dir)

        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["starting_iteration"] == 1

    def test_returns_empty_strokes_and_evaluations(self, tmp_path: Path) -> None:
        """Strokes and evaluations lists must be empty for a fresh state."""
        artwork_dir = tmp_path / "artwork-002"
        artwork_dir.mkdir()
        loader = ArtworkStateLoader(artwork_dir=artwork_dir)

        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["strokes"] == []
        assert state["evaluations"] == []

    def test_all_counters_are_zero(self, tmp_path: Path) -> None:
        """All numeric counters must be zero for a fresh state."""
        artwork_dir = tmp_path / "artwork-003"
        artwork_dir.mkdir()
        loader = ArtworkStateLoader(artwork_dir=artwork_dir)

        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["total_strokes_applied"] == 0
        assert state["total_strokes_requested"] == 0
        assert state["total_strokes_skipped"] == 0
        assert state["current_layer_index"] == 0
        assert state["stroke_type_counts"] == {}
        assert state["layer_iterations"] == {}
        assert state["painting_plan"] is None


# ---------------------------------------------------------------------------
# Batch-file loading
# ---------------------------------------------------------------------------


class TestBatchFileLoading:
    """Tests for ArtworkStateLoader when batch files exist."""

    def test_starting_iteration_is_batch_count_plus_one(self, tmp_path: Path) -> None:
        """starting_iteration should equal number-of-batches + 1."""
        artwork_dir = tmp_path / "artwork-batch"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        _write_batch_file(strokes_dir, 1, [_make_stroke()])
        _write_batch_file(strokes_dir, 2, [_make_stroke()])
        _write_batch_file(strokes_dir, 3, [_make_stroke()])

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["starting_iteration"] == 4

    def test_strokes_list_populated_from_applied_results(self, tmp_path: Path) -> None:
        """Strokes from successful results should appear in the strokes list."""
        artwork_dir = tmp_path / "artwork-batch2"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        strokes = [_make_stroke("line"), _make_stroke("arc")]
        _write_batch_file(strokes_dir, 1, strokes, applied=True)

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert len(state["strokes"]) == 2

    def test_skipped_strokes_not_in_strokes_list(self, tmp_path: Path) -> None:
        """Failed results must not appear in the strokes list."""
        artwork_dir = tmp_path / "artwork-batch3"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        _write_batch_file(strokes_dir, 1, [_make_stroke()], applied=False)

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["strokes"] == []

    def test_stroke_type_counts_populated(self, tmp_path: Path) -> None:
        """Stroke-type breakdown dict should reflect applied strokes."""
        artwork_dir = tmp_path / "artwork-batch4"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        strokes = [_make_stroke("line"), _make_stroke("line"), _make_stroke("circle")]
        _write_batch_file(strokes_dir, 1, strokes, applied=True)

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["stroke_type_counts"]["line"] == 2
        assert state["stroke_type_counts"]["circle"] == 1

    def test_canvas_manager_apply_stroke_called_for_each_applied_stroke(
        self, tmp_path: Path
    ) -> None:
        """apply_stroke must be called once per successfully applied stroke."""
        artwork_dir = tmp_path / "artwork-batch5"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        strokes = [_make_stroke(), _make_stroke(), _make_stroke()]
        _write_batch_file(strokes_dir, 1, strokes, applied=True)

        mock_canvas = _make_canvas_manager_mock()
        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        loader.load(canvas_manager=mock_canvas)

        assert mock_canvas.apply_stroke.call_count == 3

    def test_statistics_accumulated_across_batches(self, tmp_path: Path) -> None:
        """total_strokes_applied/requested/skipped must sum across batches."""
        artwork_dir = tmp_path / "artwork-batch6"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        _write_batch_file(
            strokes_dir, 1, [_make_stroke(), _make_stroke()], applied=True
        )
        _write_batch_file(strokes_dir, 2, [_make_stroke()], applied=False)

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["total_strokes_requested"] == 3
        assert state["total_strokes_applied"] == 2
        assert state["total_strokes_skipped"] == 1


# ---------------------------------------------------------------------------
# Legacy stroke-file loading
# ---------------------------------------------------------------------------


class TestLegacyFileLoading:
    """Tests for ArtworkStateLoader backward-compatibility with legacy files."""

    def test_starting_iteration_is_stroke_count_plus_one(self, tmp_path: Path) -> None:
        """For legacy format starting_iteration == number-of-stroke-files + 1."""
        artwork_dir = tmp_path / "artwork-legacy"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        for i in range(1, 4):
            _write_legacy_stroke_file(strokes_dir, i, _make_stroke())

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["starting_iteration"] == 4

    def test_strokes_list_populated_from_legacy_files(self, tmp_path: Path) -> None:
        """All legacy stroke files should appear in the strokes list."""
        artwork_dir = tmp_path / "artwork-legacy2"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        for i in range(1, 3):
            _write_legacy_stroke_file(strokes_dir, i, _make_stroke("line"))

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert len(state["strokes"]) == 2

    def test_legacy_total_strokes_applied_equals_file_count(
        self, tmp_path: Path
    ) -> None:
        """total_strokes_applied should equal number of legacy files."""
        artwork_dir = tmp_path / "artwork-legacy3"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        for i in range(1, 6):
            _write_legacy_stroke_file(strokes_dir, i, _make_stroke())

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["total_strokes_applied"] == 5
        assert state["total_strokes_requested"] == 5

    def test_canvas_apply_stroke_called_for_each_legacy_stroke(
        self, tmp_path: Path
    ) -> None:
        """apply_stroke must be called once per legacy stroke file."""
        artwork_dir = tmp_path / "artwork-legacy4"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        for i in range(1, 4):
            _write_legacy_stroke_file(strokes_dir, i, _make_stroke())

        mock_canvas = _make_canvas_manager_mock()
        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        loader.load(canvas_manager=mock_canvas)

        assert mock_canvas.apply_stroke.call_count == 3


# ---------------------------------------------------------------------------
# Evaluation loading
# ---------------------------------------------------------------------------


class TestEvaluationLoading:
    """Tests for evaluation loading regardless of stroke format."""

    def test_evaluations_loaded_from_eval_dir(self, tmp_path: Path) -> None:
        """Evaluation files in evaluations/ must be loaded into the state."""
        artwork_dir = tmp_path / "artwork-eval"
        strokes_dir, eval_dir = _setup_dirs(artwork_dir)

        _write_batch_file(strokes_dir, 1, [_make_stroke()])
        _write_evaluation_file(eval_dir, 1)
        _write_evaluation_file(eval_dir, 2)

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert len(state["evaluations"]) == 2

    def test_evaluations_empty_when_no_eval_dir(self, tmp_path: Path) -> None:
        """When no evaluations/ directory exists, evaluations must be empty."""
        artwork_dir = tmp_path / "artwork-eval2"
        strokes_dir = artwork_dir / "strokes"
        strokes_dir.mkdir(parents=True)

        _write_batch_file(strokes_dir, 1, [_make_stroke()])

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["evaluations"] == []


# ---------------------------------------------------------------------------
# Painting plan loading
# ---------------------------------------------------------------------------


class TestPaintingPlanLoading:
    """Tests for ArtworkStateLoader loading of painting_plan.json."""

    def test_painting_plan_loaded_from_file(self, tmp_path: Path) -> None:
        """painting_plan should be populated when painting_plan.json is present."""
        artwork_dir = tmp_path / "artwork-plan"
        artwork_dir.mkdir()
        plan = {
            "layers": [
                {"layer_number": 1, "name": "Background"},
            ]
        }
        with open(artwork_dir / "painting_plan.json", "w", encoding="utf-8") as f:
            json.dump(plan, f)

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["painting_plan"] is not None
        assert "layers" in state["painting_plan"]


# ---------------------------------------------------------------------------
# Layer tracking
# ---------------------------------------------------------------------------


class TestLayerTracking:
    """Tests for layer iteration tracking in ArtworkStateLoader."""

    def test_layer_iterations_populated_from_batch_files(self, tmp_path: Path) -> None:
        """layer_iterations should count how many batches belong to each layer."""
        artwork_dir = tmp_path / "artwork-layer-iter"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        plan = {
            "layers": [
                {"layer_number": 1, "name": "Background"},
            ]
        }
        with open(artwork_dir / "painting_plan.json", "w", encoding="utf-8") as f:
            json.dump(plan, f)

        _write_batch_file(strokes_dir, 1, [_make_stroke()], layer_number=1)
        _write_batch_file(strokes_dir, 2, [_make_stroke()], layer_number=1)

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["layer_iterations"][1] == 2

    def test_current_layer_index_set_from_last_batch(self, tmp_path: Path) -> None:
        """current_layer_index should reflect the layer of the most recent batch."""
        artwork_dir = tmp_path / "artwork-layer-idx"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        plan = {
            "layers": [
                {"layer_number": 1, "name": "Background"},
                {"layer_number": 2, "name": "Midground"},
            ]
        }
        with open(artwork_dir / "painting_plan.json", "w", encoding="utf-8") as f:
            json.dump(plan, f)

        _write_batch_file(strokes_dir, 1, [_make_stroke()], layer_number=1)
        _write_batch_file(strokes_dir, 2, [_make_stroke()], layer_number=2)

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        state = loader.load(canvas_manager=_make_canvas_manager_mock())

        assert state["current_layer_index"] == 1


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for ArtworkStateLoader error handling on corrupt files."""

    def test_corrupted_batch_file_raises(self, tmp_path: Path) -> None:
        """A JSON-corrupt batch file should cause load() to raise an exception."""
        artwork_dir = tmp_path / "artwork-corrupt"
        strokes_dir, _ = _setup_dirs(artwork_dir)

        _write_batch_file(strokes_dir, 1, [_make_stroke()])
        corrupt_path = strokes_dir / "iteration-002_batch.json"
        corrupt_path.write_text("not valid json", encoding="utf-8")

        loader = ArtworkStateLoader(artwork_dir=artwork_dir)
        with pytest.raises(Exception):
            loader.load(canvas_manager=_make_canvas_manager_mock())
