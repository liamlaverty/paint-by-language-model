"""Tests for evaluation prompt with painting plan context."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from models.painting_plan import PaintingPlan
from services.evaluation_vlm_client import EvaluationVLMClient


@pytest.fixture
def mock_vlm_client() -> Mock:
    """Create a mock VLMClient."""
    with patch("services.evaluation_vlm_client.VLMClient") as mock_client_class:
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def eval_client(mock_vlm_client: Mock) -> EvaluationVLMClient:
    """Create an EvaluationVLMClient with mocked VLMClient."""
    return EvaluationVLMClient(
        base_url="http://test.com",
        model="test-model",
        timeout=60,
        api_key="test-key",
        temperature=0.3,
    )


@pytest.fixture
def sample_plan() -> PaintingPlan:
    """Create a sample painting plan for testing."""
    return {
        "artist_name": "Test Artist",
        "subject": "Test Subject",
        "expanded_subject": None,
        "total_layers": 3,
        "layers": [
            {
                "layer_number": 1,
                "name": "Background",
                "description": "Paint background layer",
                "colour_palette": ["#0000FF", "#4444FF"],
                "stroke_types": ["line"],
                "techniques": "Broad strokes",
                "shapes": "Horizontal bands",
                "highlights": "Even lighting",
            },
            {
                "layer_number": 2,
                "name": "Midground",
                "description": "Paint midground elements",
                "colour_palette": ["#00FF00"],
                "stroke_types": ["arc"],
                "techniques": "Medium strokes",
                "shapes": "Curved forms",
                "highlights": "Soft shadows",
            },
            {
                "layer_number": 3,
                "name": "Foreground",
                "description": "Paint foreground details",
                "colour_palette": ["#FF0000"],
                "stroke_types": ["circle"],
                "techniques": "Fine detail",
                "shapes": "Small circles",
                "highlights": "Sharp focus",
            },
        ],
        "overall_notes": "Test plan",
    }


class TestLayerContextInPrompt:
    """Tests for layer context inclusion in evaluation prompt."""

    def test_prompt_does_not_include_layer_number_or_name(
        self, eval_client: EvaluationVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Layer number and name are no longer injected into the evaluation prompt."""
        current_layer = sample_plan["layers"][1]

        prompt = eval_client._build_evaluation_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=10,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert f"Layer {current_layer['layer_number']}" not in prompt
        assert current_layer["name"] not in prompt

    def test_prompt_does_not_include_total_layers_count(
        self, eval_client: EvaluationVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Total layer count is no longer injected into the evaluation prompt."""
        current_layer = sample_plan["layers"][1]

        prompt = eval_client._build_evaluation_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=10,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert f"{sample_plan['total_layers']} layers" not in prompt

    def test_prompt_does_not_include_layer_description(
        self, eval_client: EvaluationVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Layer description is no longer injected into the evaluation prompt."""
        current_layer = sample_plan["layers"][1]

        prompt = eval_client._build_evaluation_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=10,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["description"] not in prompt

    def test_prompt_does_not_include_expected_palette(
        self, eval_client: EvaluationVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Expected palette is no longer injected into the evaluation prompt."""
        current_layer = sample_plan["layers"][1]

        prompt = eval_client._build_evaluation_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=10,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "Expected palette:" not in prompt
        for color in current_layer["colour_palette"]:
            assert color not in prompt

    def test_prompt_does_not_include_expected_techniques(
        self, eval_client: EvaluationVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Expected techniques are no longer injected into the evaluation prompt."""
        current_layer = sample_plan["layers"][1]

        prompt = eval_client._build_evaluation_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=10,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "Expected techniques:" not in prompt
        assert current_layer["techniques"] not in prompt

    def test_prompt_does_not_request_layer_complete_field(
        self, eval_client: EvaluationVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt does NOT request layer_complete field in response format."""
        current_layer = sample_plan["layers"][1]

        prompt = eval_client._build_evaluation_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=10,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "layer_complete" not in prompt

    def test_prompt_unchanged_when_layer_is_none(
        self, eval_client: EvaluationVLMClient
    ) -> None:
        """Test that prompt is unchanged when current_layer is None."""
        prompt = eval_client._build_evaluation_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=10,
            painting_plan=None,
            current_layer=None,
        )

        assert (
            "Layer" not in prompt or "Iteration" in prompt
        )  # "Iteration" has "Layer" substring
        assert "layer_complete" not in prompt


class TestEvaluationResponseParsing:
    """Tests for evaluation response parsing with layer context."""

    def test_layer_number_included_when_provided(
        self, eval_client: EvaluationVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that layer_number is included in result when provided."""
        import json

        current_layer = sample_plan["layers"][2]
        response = json.dumps(
            {
                "score": 80.0,
                "feedback": "Excellent",
                "strengths": "Very good",
                "suggestions": "Minor tweaks",
                "layer_complete": True,
            }
        )

        result = eval_client._parse_evaluation_response(
            response_text=response,
            iteration=15,
            current_layer=current_layer,
        )

        assert result.get("layer_number") == 3

    def test_response_without_layer_context_works(
        self, eval_client: EvaluationVLMClient
    ) -> None:
        """Test that EvaluationResult without layer_complete field works (backward compat)."""
        import json

        response = json.dumps(
            {
                "score": 70.0,
                "feedback": "Progress made",
                "strengths": "Good technique",
                "suggestions": "Keep going",
            }
        )

        result = eval_client._parse_evaluation_response(
            response_text=response,
            iteration=10,
            current_layer=None,
        )

        assert result["score"] == 70.0
        assert "layer_complete" not in result
        assert "layer_number" not in result
