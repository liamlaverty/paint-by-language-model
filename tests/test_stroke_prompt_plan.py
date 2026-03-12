"""Tests for stroke prompt with painting plan context."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from models.painting_plan import PaintingPlan
from services.stroke_vlm_client import StrokeVLMClient


@pytest.fixture
def mock_vlm_client() -> Mock:
    """Create a mock VLMClient."""
    with patch("services.stroke_vlm_client.VLMClient") as mock_client_class:
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def stroke_client(mock_vlm_client: Mock) -> StrokeVLMClient:
    """Create a StrokeVLMClient with mocked VLMClient."""
    return StrokeVLMClient(
        base_url="http://test.com",
        model="test-model",
        timeout=60,
        api_key="test_key",
        temperature=0.7,
    )


@pytest.fixture
def sample_plan() -> PaintingPlan:
    """Create a sample painting plan for testing."""
    return {
        "artist_name": "Test Artist",
        "subject": "Test Subject",
        "expanded_subject": "Detailed test description",
        "total_layers": 2,
        "layers": [
            {
                "layer_number": 1,
                "name": "Background",
                "description": "Paint a blue background",
                "colour_palette": ["#0000FF", "#4444FF"],
                "stroke_types": ["line", "arc"],
                "techniques": "Broad strokes",
                "shapes": "Horizontal bands",
                "highlights": "Even lighting",
            },
            {
                "layer_number": 2,
                "name": "Foreground",
                "description": "Paint foreground details",
                "colour_palette": ["#FF0000"],
                "stroke_types": ["circle"],
                "techniques": "Fine detail",
                "shapes": "Small circles",
                "highlights": "Center focus",
            },
        ],
        "overall_notes": "Test plan",
    }


class TestPlanContextInPrompt:
    """Tests for plan context inclusion in stroke prompt."""

    def test_prompt_includes_full_plan_json(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes full plan JSON when painting_plan is provided."""
        current_layer = sample_plan["layers"][0]

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "=== PAINTING PLAN ===" in prompt
        assert json.dumps(sample_plan, indent=2) in prompt

    def test_prompt_includes_current_focus_section(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes 'CURRENT FOCUS' section with active layer details."""
        current_layer = sample_plan["layers"][0]

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "=== CURRENT FOCUS ===" in prompt
        assert 'Layer 1: "Background"' in prompt

    def test_prompt_includes_layer_description(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer description."""
        current_layer = sample_plan["layers"][0]

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["description"] in prompt

    def test_prompt_includes_layer_palette(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer colour palette."""
        current_layer = sample_plan["layers"][0]

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        for color in current_layer["colour_palette"]:
            assert color in prompt

    def test_prompt_includes_layer_techniques(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer techniques."""
        current_layer = sample_plan["layers"][0]

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["techniques"] in prompt

    def test_prompt_includes_layer_shapes(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer shapes."""
        current_layer = sample_plan["layers"][0]

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["shapes"] in prompt

    def test_prompt_includes_layer_highlights(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer highlights."""
        current_layer = sample_plan["layers"][0]

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["highlights"] in prompt

    def test_prompt_unchanged_when_plan_is_none(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that prompt is unchanged when painting_plan is None."""
        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=None,
            current_layer=None,
        )

        assert "=== PAINTING PLAN ===" not in prompt
        assert "=== CURRENT FOCUS ===" not in prompt


class TestExpandedSubjectInPrompt:
    """Tests for expanded subject inclusion in stroke prompt."""

    def test_prompt_includes_expanded_subject_when_provided(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that prompt includes 'Detailed description:' when expanded_subject is provided."""
        expanded = "A very detailed description of the painting"

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            expanded_subject=expanded,
        )

        assert "Detailed description:" in prompt
        assert expanded in prompt

    def test_prompt_omits_expanded_subject_when_none(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that prompt omits expanded subject when None."""
        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            expanded_subject=None,
        )

        assert "Detailed description:" not in prompt


class TestLayerCompleteInPromptAndParsing:
    """Tests for layer_complete field in stroke prompt and response parsing."""

    def test_stroke_prompt_includes_layer_complete_field_when_layer_provided(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer_complete field when current_layer is provided."""
        current_layer = sample_plan["layers"][0]

        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "layer_complete" in prompt

    def test_stroke_prompt_excludes_layer_complete_when_no_layer(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt does NOT include layer_complete when current_layer is None."""
        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=None,
            current_layer=None,
        )

        assert "layer_complete" not in prompt

    def test_stroke_prompt_excludes_layer_complete_when_plan_provided_but_no_layer(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt does NOT include layer_complete when painting_plan is set but current_layer is None."""
        prompt = stroke_client._build_stroke_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=None,
        )

        assert "layer_complete" not in prompt

    def test_parse_stroke_response_with_layer_complete_true(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that parser.parse() returns layer_complete True when present."""
        import json

        response_text = json.dumps(
            {
                "strokes": [],
                "updated_strategy": None,
                "batch_reasoning": "Test reasoning",
                "layer_complete": True,
            }
        )

        result = stroke_client.parser.parse(response_text)

        assert result.get("layer_complete") is True

    def test_parse_stroke_response_with_layer_complete_false(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that parser.parse() returns layer_complete False when present."""
        import json

        response_text = json.dumps(
            {
                "strokes": [],
                "updated_strategy": None,
                "batch_reasoning": "Test reasoning",
                "layer_complete": False,
            }
        )

        result = stroke_client.parser.parse(response_text)

        assert result.get("layer_complete") is False

    def test_parse_stroke_response_without_layer_complete(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that parser.parse() omits layer_complete when absent in response."""
        import json

        response_text = json.dumps(
            {
                "strokes": [],
                "updated_strategy": None,
                "batch_reasoning": "Test reasoning",
            }
        )

        result = stroke_client.parser.parse(response_text)

        assert "layer_complete" not in result
