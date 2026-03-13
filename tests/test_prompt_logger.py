"""Tests for PromptLogger and its integration with VLM/LLM clients."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.prompt_logger import PromptLogger

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

_PLAN_JSON = json.dumps(
    {
        "artist_name": "Test Artist",
        "subject": "Test Subject",
        "expanded_subject": None,
        "total_layers": 2,
        "layers": [
            {
                "layer_number": 1,
                "name": "Background",
                "description": "Paint the background",
                "colour_palette": ["#FF5733"],
                "stroke_types": ["line"],
                "techniques": "Broad strokes",
                "shapes": "Horizontal bands",
                "highlights": "Top-left lighting",
                "min_iterations": 3,
                "max_iterations": 8,
            },
            {
                "layer_number": 2,
                "name": "Foreground",
                "description": "Paint the foreground",
                "colour_palette": ["#33FF57"],
                "stroke_types": ["arc"],
                "techniques": "Fine strokes",
                "shapes": "Vertical lines",
                "highlights": "Bottom-right lighting",
                "min_iterations": 3,
                "max_iterations": 8,
            },
        ],
    }
)

_STROKE_JSON = json.dumps(
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
        "batch_reasoning": "Test reasoning",
    }
)

_EVAL_JSON = json.dumps(
    {
        "score": 72.5,
        "feedback": "Good work",
        "strengths": "Color palette",
        "suggestions": "More texture",
    }
)


# ---------------------------------------------------------------------------
# Unit tests: PromptLogger in isolation
# ---------------------------------------------------------------------------


class TestPromptLoggerInit:
    """Tests for PromptLogger.__init__."""

    def test_creates_log_directory(self, tmp_path: Path) -> None:
        """PromptLogger.__init__ creates the prompt-log subdirectory."""
        artwork_dir = tmp_path / "my-artwork"
        logger = PromptLogger(artwork_dir=artwork_dir)

        assert logger.log_dir.exists()
        assert logger.log_dir.is_dir()
        assert logger.log_dir == artwork_dir / "prompt-log"

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """PromptLogger creates all intermediate parent directories."""
        artwork_dir = tmp_path / "nested" / "path" / "artwork"
        logger = PromptLogger(artwork_dir=artwork_dir)

        assert logger.log_dir.exists()

    def test_idempotent_on_existing_directory(self, tmp_path: Path) -> None:
        """PromptLogger does not raise if the log directory already exists."""
        artwork_dir = tmp_path / "artwork"
        (artwork_dir / "prompt-log").mkdir(parents=True)

        # Should not raise
        logger = PromptLogger(artwork_dir=artwork_dir)
        assert logger.log_dir.exists()


# ---------------------------------------------------------------------------
# Unit tests: log_interaction()
# ---------------------------------------------------------------------------


class TestLogInteraction:
    """Tests for PromptLogger.log_interaction()."""

    def _make_logger(self, tmp_path: Path) -> PromptLogger:
        return PromptLogger(artwork_dir=tmp_path / "artwork")

    def test_writes_json_file(self, tmp_path: Path) -> None:
        """log_interaction() writes a file to the log directory."""
        pl = self._make_logger(tmp_path)
        path = pl.log_interaction(
            prompt_type="stroke",
            prompt="test prompt",
            raw_response="test response",
            model="test-model",
            provider="testprovider",
            temperature=0.7,
        )

        assert path.exists()
        assert path.suffix == ".json"

    def test_json_contains_all_required_fields(self, tmp_path: Path) -> None:
        """log_interaction() JSON file contains every required top-level field."""
        pl = self._make_logger(tmp_path)
        context = {"iteration": 3, "artist_name": "Monet"}
        images = [{"label": "Current canvas", "size_bytes": 1024}]

        path = pl.log_interaction(
            prompt_type="stroke",
            prompt="my prompt text",
            raw_response="raw llm output",
            model="claude-sonnet-4-6",
            provider="anthropic",
            temperature=0.9,
            images=images,
            context=context,
        )

        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)

        assert data["type"] == "stroke"
        assert data["model"] == "claude-sonnet-4-6"
        assert data["provider"] == "anthropic"
        assert data["temperature"] == 0.9
        assert data["prompt"] == "my prompt text"
        assert data["raw_response"] == "raw llm output"
        assert data["images"] == images
        assert data["context"] == context
        assert "timestamp" in data

    def test_returns_path_to_saved_file(self, tmp_path: Path) -> None:
        """log_interaction() returns the Path of the file it wrote."""
        pl = self._make_logger(tmp_path)
        path = pl.log_interaction(
            prompt_type="plan",
            prompt="p",
            raw_response="r",
            model="m",
            provider="prov",
            temperature=0.5,
        )

        assert isinstance(path, Path)
        assert path.is_file()

    def test_images_none_serialises_as_null(self, tmp_path: Path) -> None:
        """When images=None, the JSON field is null."""
        pl = self._make_logger(tmp_path)
        path = pl.log_interaction(
            prompt_type="plan",
            prompt="p",
            raw_response="r",
            model="m",
            provider="prov",
            temperature=0.5,
            images=None,
        )

        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)

        assert data["images"] is None

    def test_context_none_serialises_as_null(self, tmp_path: Path) -> None:
        """When context=None, the JSON field is null."""
        pl = self._make_logger(tmp_path)
        path = pl.log_interaction(
            prompt_type="evaluation",
            prompt="p",
            raw_response="r",
            model="m",
            provider="prov",
            temperature=0.3,
            context=None,
        )

        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)

        assert data["context"] is None

    def test_file_is_stored_inside_log_dir(self, tmp_path: Path) -> None:
        """log_interaction() writes the file inside the prompt-log directory."""
        pl = self._make_logger(tmp_path)
        path = pl.log_interaction(
            prompt_type="stroke",
            prompt="p",
            raw_response="r",
            model="m",
            provider="prov",
            temperature=0.7,
        )

        assert path.parent == pl.log_dir


# ---------------------------------------------------------------------------
# Unit tests: _generate_filename()
# ---------------------------------------------------------------------------

_FILENAME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{6}-[a-z]+\.json$"
)


class TestGenerateFilename:
    """Tests for PromptLogger._generate_filename()."""

    def test_filename_matches_expected_pattern(self, tmp_path: Path) -> None:
        """_generate_filename() returns a string matching the documented format."""
        pl = PromptLogger(artwork_dir=tmp_path / "artwork")
        filename = pl._generate_filename("stroke")

        assert _FILENAME_PATTERN.match(filename), (
            f"Filename '{filename}' does not match expected pattern "
            r"YYYY-MM-DDTHH-MM-SS-<microseconds>-<type>.json"
        )

    def test_filename_contains_prompt_type(self, tmp_path: Path) -> None:
        """_generate_filename() embeds the prompt_type in the filename."""
        pl = PromptLogger(artwork_dir=tmp_path / "artwork")

        for prompt_type in ("plan", "stroke", "evaluation"):
            filename = pl._generate_filename(prompt_type)
            assert filename.endswith(f"-{prompt_type}.json"), (
                f"Filename '{filename}' does not end with '-{prompt_type}.json'"
            )

    def test_no_collision_on_rapid_calls(self, tmp_path: Path) -> None:
        """Two rapid log_interaction() calls produce two distinct files."""
        pl = PromptLogger(artwork_dir=tmp_path / "artwork")

        path1 = pl.log_interaction(
            prompt_type="stroke",
            prompt="p1",
            raw_response="r1",
            model="m",
            provider="prov",
            temperature=0.7,
        )
        path2 = pl.log_interaction(
            prompt_type="stroke",
            prompt="p2",
            raw_response="r2",
            model="m",
            provider="prov",
            temperature=0.7,
        )

        assert path1 != path2, "Two calls should produce distinct file paths"
        assert path1.exists()
        assert path2.exists()


# ---------------------------------------------------------------------------
# Integration tests with StrokeVLMClient
# ---------------------------------------------------------------------------


class TestPromptLoggerWithStrokeVLMClient:
    """Integration tests between PromptLogger and StrokeVLMClient."""

    def test_stroke_log_file_written_on_suggest_strokes(self, tmp_path: Path) -> None:
        """suggest_strokes() writes a 'stroke' log file when prompt_logger is set."""
        from services.clients.stroke_vlm_client import StrokeVLMClient

        artwork_dir = tmp_path / "artwork"
        pl = PromptLogger(artwork_dir=artwork_dir)

        client = StrokeVLMClient(prompt_logger=pl)

        with patch.object(
            client.client,
            "query_multimodal_multi_image",
            return_value=_STROKE_JSON,
        ):
            client.suggest_strokes(
                canvas_image=b"fake_canvas",
                artist_name="Monet",
                subject="Pond",
                iteration=1,
            )

        log_files = list(pl.log_dir.glob("*-stroke.json"))
        assert len(log_files) == 1, f"Expected 1 stroke log, found {len(log_files)}"

        with open(log_files[0], encoding="utf-8") as fh:
            data = json.load(fh)

        assert data["type"] == "stroke"
        assert data["context"]["artist_name"] == "Monet"
        assert data["context"]["subject"] == "Pond"
        assert data["context"]["iteration"] == 1
        assert "num_strokes_requested" in data["context"]
        assert "num_strokes_parsed" in data["context"]
        assert data["images"] is not None
        assert any(img["label"] == "Current canvas" for img in data["images"])

    def test_no_log_file_when_no_prompt_logger(self, tmp_path: Path) -> None:
        """suggest_strokes() does not error and writes no log when prompt_logger is None."""
        from services.clients.stroke_vlm_client import StrokeVLMClient

        client = StrokeVLMClient()

        log_dir = tmp_path / "no_logs"
        log_dir.mkdir()

        with patch.object(
            client.client,
            "query_multimodal_multi_image",
            return_value=_STROKE_JSON,
        ):
            client.suggest_strokes(
                canvas_image=b"fake_canvas",
                artist_name="Monet",
                subject="Pond",
                iteration=1,
            )

        assert list(log_dir.glob("*.json")) == []


# ---------------------------------------------------------------------------
# Integration tests with EvaluationVLMClient
# ---------------------------------------------------------------------------


class TestPromptLoggerWithEvaluationVLMClient:
    """Integration tests between PromptLogger and EvaluationVLMClient."""

    def test_evaluation_log_file_written_on_evaluate_style(
        self, tmp_path: Path
    ) -> None:
        """evaluate_style() writes an 'evaluation' log file when prompt_logger is set."""
        from services.clients.evaluation_vlm_client import EvaluationVLMClient

        artwork_dir = tmp_path / "artwork"
        pl = PromptLogger(artwork_dir=artwork_dir)

        client = EvaluationVLMClient(prompt_logger=pl)

        with patch.object(
            client.client,
            "query_multimodal",
            return_value=_EVAL_JSON,
        ):
            client.evaluate_style(
                canvas_image=b"fake_canvas_bytes",
                artist_name="Renoir",
                subject="Garden",
                iteration=5,
            )

        log_files = list(pl.log_dir.glob("*-evaluation.json"))
        assert len(log_files) == 1, f"Expected 1 evaluation log, found {len(log_files)}"

        with open(log_files[0], encoding="utf-8") as fh:
            data = json.load(fh)

        assert data["type"] == "evaluation"
        assert data["context"]["artist_name"] == "Renoir"
        assert data["context"]["subject"] == "Garden"
        assert data["context"]["iteration"] == 5
        assert data["context"]["score"] == 72.5
        assert data["images"] is not None
        assert data["images"][0]["label"] == "Current canvas"
        assert data["images"][0]["size_bytes"] == len(b"fake_canvas_bytes")

    def test_no_log_file_when_no_prompt_logger_eval(self, tmp_path: Path) -> None:
        """evaluate_style() does not error when prompt_logger is None."""
        from services.clients.evaluation_vlm_client import EvaluationVLMClient

        client = EvaluationVLMClient()

        with patch.object(
            client.client,
            "query_multimodal",
            return_value=_EVAL_JSON,
        ):
            result = client.evaluate_style(
                canvas_image=b"fake_canvas_bytes",
                artist_name="Renoir",
                subject="Garden",
                iteration=5,
            )

        assert result["score"] == 72.5


# ---------------------------------------------------------------------------
# Integration tests with PlannerLLMClient
# ---------------------------------------------------------------------------


class TestPromptLoggerWithPlannerLLMClient:
    """Integration tests between PromptLogger and PlannerLLMClient."""

    def test_plan_log_file_written_on_generate_plan(self, tmp_path: Path) -> None:
        """generate_plan() writes a 'plan' log file when prompt_logger is set."""
        from services.clients.planner_llm_client import PlannerLLMClient

        artwork_dir = tmp_path / "artwork"
        pl = PromptLogger(artwork_dir=artwork_dir)

        with patch("services.clients.planner_llm_client.VLMClient") as MockVLMClient:
            mock_instance = Mock()
            mock_instance.query.return_value = _PLAN_JSON
            mock_instance.provider = "anthropic"
            mock_instance.temperature = 0.4
            MockVLMClient.return_value = mock_instance

            client = PlannerLLMClient(prompt_logger=pl)
            client.generate_plan(
                artist_name="Cézanne",
                subject="Still Life",
                expanded_subject=None,
                stroke_types=["line", "arc"],
            )

        log_files = list(pl.log_dir.glob("*-plan.json"))
        assert len(log_files) == 1, f"Expected 1 plan log, found {len(log_files)}"

        with open(log_files[0], encoding="utf-8") as fh:
            data = json.load(fh)

        assert data["type"] == "plan"
        assert data["context"]["artist_name"] == "Cézanne"
        assert data["context"]["subject"] == "Still Life"
        assert data["context"]["layer_count"] == 2
        assert data["images"] is None

    def test_no_log_file_when_no_prompt_logger_plan(self, tmp_path: Path) -> None:
        """generate_plan() does not error when prompt_logger is None."""
        from services.clients.planner_llm_client import PlannerLLMClient

        with patch("services.clients.planner_llm_client.VLMClient") as MockVLMClient:
            mock_instance = Mock()
            mock_instance.query.return_value = _PLAN_JSON
            mock_instance.provider = "lmstudio"
            mock_instance.temperature = 0.4
            MockVLMClient.return_value = mock_instance

            client = PlannerLLMClient()
            plan = client.generate_plan(
                artist_name="Cézanne",
                subject="Still Life",
                expanded_subject=None,
                stroke_types=["line"],
            )

        assert plan["total_layers"] == 2
