"""Unit tests for ArtworkPersistence service."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.artwork_persistence import ArtworkPersistence

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_persistence(tmp_path: Path) -> ArtworkPersistence:
    """Create an ArtworkPersistence instance rooted in *tmp_path*.

    Args:
        tmp_path (Path): Pytest tmp_path fixture directory.

    Returns:
        ArtworkPersistence: Configured persistence instance.
    """
    artwork_id = "test-artwork-001"
    artwork_dir = tmp_path / artwork_id
    artwork_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories that would normally be created by the orchestrator
    (artwork_dir / "evaluations").mkdir(exist_ok=True)
    (artwork_dir / "strokes").mkdir(exist_ok=True)

    return ArtworkPersistence(
        artwork_dir=artwork_dir,
        artwork_id=artwork_id,
        output_dir=tmp_path,
    )


def _make_evaluation(iteration: int = 1) -> dict:
    """Build a minimal EvaluationResult-compatible dict.

    Args:
        iteration (int): The iteration number to embed.

    Returns:
        dict: A minimal evaluation dict.
    """
    return {
        "iteration": iteration,
        "score": 42.0,
        "feedback": "Looking good",
        "strengths": "Colour balance",
        "suggestions": "More contrast",
        "weaknesses": "Flat highlights",
    }


def _make_stroke(stroke_type: str = "line") -> dict:
    """Build a minimal Stroke-compatible dict.

    Args:
        stroke_type (str): Stroke type string.

    Returns:
        dict: A minimal stroke dict.
    """
    return {
        "type": stroke_type,
        "x1": 10,
        "y1": 10,
        "x2": 100,
        "y2": 100,
        "color": "#FF0000",
        "thickness": 3,
        "opacity": 0.8,
        "reasoning": "Test stroke",
    }


# ---------------------------------------------------------------------------
# save_evaluation
# ---------------------------------------------------------------------------


class TestSaveEvaluation:
    """Tests for ArtworkPersistence.save_evaluation."""

    def test_creates_correctly_named_file(self, tmp_path: Path) -> None:
        """save_evaluation should write iteration-NNN.json into evaluations/."""
        persistence = _make_persistence(tmp_path)
        evaluation = _make_evaluation(iteration=3)

        persistence.save_evaluation(evaluation)

        expected = persistence.artwork_dir / "evaluations" / "iteration-003.json"
        assert expected.exists(), "Expected evaluation file was not created"

    def test_file_contains_correct_data(self, tmp_path: Path) -> None:
        """The written file should be valid JSON matching the evaluation dict."""
        persistence = _make_persistence(tmp_path)
        evaluation = _make_evaluation(iteration=7)

        persistence.save_evaluation(evaluation)

        filepath = persistence.artwork_dir / "evaluations" / "iteration-007.json"
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert data["iteration"] == 7
        assert data["score"] == pytest.approx(42.0)
        assert data["feedback"] == "Looking good"

    def test_zero_pads_iteration_to_three_digits(self, tmp_path: Path) -> None:
        """Iteration numbers should be zero-padded to three digits."""
        persistence = _make_persistence(tmp_path)
        persistence.save_evaluation(_make_evaluation(iteration=1))

        filepath = persistence.artwork_dir / "evaluations" / "iteration-001.json"
        assert filepath.exists()


def _make_results(strokes: list) -> list:
    """Build fake application results for a list of strokes.

    Args:
        strokes (list): The stroke list the results correspond to.

    Returns:
        list: A list of result dicts with ``index``, ``success``, and
            ``error`` keys.
    """
    return [{"index": i, "success": True, "error": None} for i in range(len(strokes))]


# ---------------------------------------------------------------------------
# save_stroke_batch
# ---------------------------------------------------------------------------


class TestSaveStrokeBatch:
    """Tests for ArtworkPersistence.save_stroke_batch."""

    def test_creates_batch_json_file(self, tmp_path: Path) -> None:
        """save_stroke_batch should write iteration-NNN_batch.json."""
        persistence = _make_persistence(tmp_path)
        strokes = [_make_stroke("line"), _make_stroke("arc")]
        results = _make_results(strokes)

        persistence.save_stroke_batch(
            strokes=strokes,
            iteration=2,
            batch_reasoning="Test batch",
            results=results,
        )

        expected = persistence.artwork_dir / "strokes" / "iteration-002_batch.json"
        assert expected.exists()

    def test_batch_file_has_expected_keys(self, tmp_path: Path) -> None:
        """The batch JSON must contain the standard metadata keys."""
        persistence = _make_persistence(tmp_path)
        strokes = [_make_stroke("circle")]
        results = _make_results(strokes)

        persistence.save_stroke_batch(
            strokes=strokes,
            iteration=5,
            batch_reasoning="Round shapes",
            results=results,
        )

        fp = persistence.artwork_dir / "strokes" / "iteration-005_batch.json"
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)

        for key in (
            "iteration",
            "strokes",
            "batch_reasoning",
            "applied_count",
            "skipped_count",
            "total_requested",
            "timestamp",
            "results",
        ):
            assert key in data, f"Expected key '{key}' missing from batch JSON"

    def test_applied_and_skipped_counts_are_correct(self, tmp_path: Path) -> None:
        """applied_count and skipped_count should reflect the results list."""
        persistence = _make_persistence(tmp_path)
        strokes = [_make_stroke(), _make_stroke(), _make_stroke()]
        results = [
            {"index": 0, "success": True, "error": None},
            {"index": 1, "success": False, "error": "out of bounds"},
            {"index": 2, "success": True, "error": None},
        ]

        persistence.save_stroke_batch(
            strokes=strokes,
            iteration=1,
            batch_reasoning="Mixed batch",
            results=results,
        )

        fp = persistence.artwork_dir / "strokes" / "iteration-001_batch.json"
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)

        assert data["applied_count"] == 2
        assert data["skipped_count"] == 1
        assert data["total_requested"] == 3


# ---------------------------------------------------------------------------
# log_exception
# ---------------------------------------------------------------------------


class TestLogException:
    """Tests for ArtworkPersistence.log_exception."""

    def test_creates_log_file(self, tmp_path: Path) -> None:
        """log_exception should create a .log file under exception_logs/."""
        persistence = _make_persistence(tmp_path)
        exc = ValueError("something went wrong")

        persistence.log_exception(iteration=4, exception=exc, error_type="evaluation")

        log_dir = tmp_path / "exception_logs" / "test-artwork-001"
        log_files = list(log_dir.glob("iteration-004_evaluation_*.log"))
        assert len(log_files) == 1, "Expected exactly one log file to be created"

    def test_log_file_contains_exception_message(self, tmp_path: Path) -> None:
        """The log file must include the exception message."""
        persistence = _make_persistence(tmp_path)
        exc = RuntimeError("VLM timed out")

        persistence.log_exception(
            iteration=1, exception=exc, error_type="stroke_generation"
        )

        log_dir = tmp_path / "exception_logs" / "test-artwork-001"
        log_file = next(log_dir.glob("iteration-001_stroke_generation_*.log"))
        content = log_file.read_text(encoding="utf-8")

        assert "VLM timed out" in content
        assert "RuntimeError" in content

    def test_log_file_contains_raw_response_when_provided(self, tmp_path: Path) -> None:
        """If raw_response is supplied it should appear in the log file."""
        persistence = _make_persistence(tmp_path)
        exc = ValueError("parse error")
        raw = '{"broken json": }'

        persistence.log_exception(
            iteration=2,
            exception=exc,
            error_type="evaluation",
            raw_response=raw,
        )

        log_dir = tmp_path / "exception_logs" / "test-artwork-001"
        log_file = next(log_dir.glob("iteration-002_evaluation_*.log"))
        content = log_file.read_text(encoding="utf-8")

        assert raw in content


# ---------------------------------------------------------------------------
# save_all_strokes
# ---------------------------------------------------------------------------


class TestSaveAllStrokes:
    """Tests for ArtworkPersistence.save_all_strokes."""

    def test_creates_all_strokes_file(self, tmp_path: Path) -> None:
        """save_all_strokes should write strokes/all_strokes.json."""
        persistence = _make_persistence(tmp_path)
        stroke1 = _make_stroke("line")
        stroke2 = _make_stroke("arc")

        persistence.save_all_strokes([stroke1, stroke2])

        expected = persistence.artwork_dir / "strokes" / "all_strokes.json"
        assert expected.exists(), "Expected all_strokes.json was not created"

    def test_file_contains_all_strokes(self, tmp_path: Path) -> None:
        """The written file should contain both strokes serialised as JSON."""
        persistence = _make_persistence(tmp_path)
        stroke1 = _make_stroke("line")
        stroke2 = _make_stroke("arc")

        persistence.save_all_strokes([stroke1, stroke2])

        filepath = persistence.artwork_dir / "strokes" / "all_strokes.json"
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["type"] == "line"
        assert data[1]["type"] == "arc"


# ---------------------------------------------------------------------------
# save_metadata
# ---------------------------------------------------------------------------


class TestSaveMetadata:
    """Tests for ArtworkPersistence.save_metadata."""

    def test_creates_metadata_file(self, tmp_path: Path) -> None:
        """save_metadata should write the file at OUTPUT_STRUCTURE['metadata']."""
        from config import OUTPUT_STRUCTURE

        persistence = _make_persistence(tmp_path)

        persistence.save_metadata({"key": "value"})

        expected = persistence.artwork_dir / OUTPUT_STRUCTURE["metadata"]
        assert expected.exists(), "Expected metadata file was not created"

    def test_file_contains_correct_data(self, tmp_path: Path) -> None:
        """The written metadata file should contain the supplied dict."""
        persistence = _make_persistence(tmp_path)
        metadata = {"artist": "Monet", "iterations": 10, "score": 87.5}

        persistence.save_metadata(metadata)

        from config import OUTPUT_STRUCTURE

        filepath = persistence.artwork_dir / OUTPUT_STRUCTURE["metadata"]
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert data["artist"] == "Monet"
        assert data["iterations"] == 10
        assert data["score"] == pytest.approx(87.5)
