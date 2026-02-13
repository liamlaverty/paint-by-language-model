"""Tests for PlannerLLMClient."""

import json
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import CANVAS_HEIGHT, CANVAS_WIDTH
from models.painting_plan import PaintingPlan
from services.planner_llm_client import PlannerLLMClient


@pytest.fixture
def mock_vlm_client() -> Mock:
    """Create a mock VLMClient."""
    with patch("services.planner_llm_client.VLMClient") as mock_client_class:
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def planner_client(mock_vlm_client: Mock) -> PlannerLLMClient:
    """Create a PlannerLLMClient with mocked VLMClient."""
    return PlannerLLMClient(
        base_url="http://test.com",
        model="test-model",
        timeout=60,
        api_key="test-key",
        temperature=0.4,
    )


class TestPromptConstruction:
    """Tests for prompt construction."""

    def test_prompt_includes_artist_name(self, planner_client: PlannerLLMClient) -> None:
        """Test that prompt includes artist name."""
        prompt = planner_client._build_planning_prompt(
            artist_name="Vincent van Gogh",
            subject="Starry Night",
            expanded_subject=None,
            stroke_types=["line", "arc"],
        )

        assert "Vincent van Gogh" in prompt

    def test_prompt_includes_subject(self, planner_client: PlannerLLMClient) -> None:
        """Test that prompt includes subject."""
        prompt = planner_client._build_planning_prompt(
            artist_name="Claude Monet",
            subject="Water Lilies",
            expanded_subject=None,
            stroke_types=["line", "arc"],
        )

        assert "Water Lilies" in prompt

    def test_prompt_includes_stroke_types(self, planner_client: PlannerLLMClient) -> None:
        """Test that prompt includes stroke types."""
        prompt = planner_client._build_planning_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            expanded_subject=None,
            stroke_types=["line", "arc", "splatter"],
        )

        assert "line" in prompt
        assert "arc" in prompt
        assert "splatter" in prompt

    def test_prompt_includes_canvas_dimensions(self, planner_client: PlannerLLMClient) -> None:
        """Test that prompt includes canvas dimensions."""
        prompt = planner_client._build_planning_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            expanded_subject=None,
            stroke_types=["line"],
        )

        assert str(CANVAS_WIDTH) in prompt
        assert str(CANVAS_HEIGHT) in prompt

    def test_prompt_includes_expanded_subject_when_provided(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that prompt includes expanded subject when provided."""
        expanded = "A detailed serene pond with floating water lilies"
        prompt = planner_client._build_planning_prompt(
            artist_name="Claude Monet",
            subject="Water Lilies",
            expanded_subject=expanded,
            stroke_types=["line"],
        )

        assert expanded in prompt
        assert "Expanded description:" in prompt

    def test_prompt_omits_expanded_subject_when_none(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that prompt omits expanded subject section when None."""
        prompt = planner_client._build_planning_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            expanded_subject=None,
            stroke_types=["line"],
        )

        assert "Expanded description:" not in prompt

    def test_prompt_requests_json_only_response(self, planner_client: PlannerLLMClient) -> None:
        """Test that prompt requests JSON-only response."""
        prompt = planner_client._build_planning_prompt(
            artist_name="Test Artist",
            subject="Test Subject",
            expanded_subject=None,
            stroke_types=["line"],
        )

        assert "RESPONSE FORMAT (JSON only)" in prompt
        assert "IMPORTANT: Respond ONLY with valid JSON" in prompt


class TestResponseParsingValid:
    """Tests for parsing valid responses."""

    def test_well_formed_json_plan_parses(self, planner_client: PlannerLLMClient) -> None:
        """Test that well-formed JSON plan with 3+ layers parses into PaintingPlan."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 3,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Background",
                        "description": "Paint the background",
                        "colour_palette": ["#FF5733", "#33FF57"],
                        "stroke_types": ["line", "arc"],
                        "techniques": "Broad strokes",
                        "shapes": "Horizontal bands",
                        "highlights": "Top-left lighting",
                    },
                    {
                        "layer_number": 2,
                        "name": "Midground",
                        "description": "Paint the midground",
                        "colour_palette": ["#3357FF"],
                        "stroke_types": ["circle"],
                        "techniques": "Dotting",
                        "shapes": "Circular forms",
                        "highlights": "Center focus",
                    },
                    {
                        "layer_number": 3,
                        "name": "Foreground",
                        "description": "Paint the foreground",
                        "colour_palette": ["#FF33F5"],
                        "stroke_types": ["polyline"],
                        "techniques": "Sharp lines",
                        "shapes": "Angular",
                        "highlights": "Strong contrast",
                    },
                ],
                "overall_notes": "Test painting plan",
            }
        )

        plan = planner_client._parse_plan_response(response)

        assert plan["artist_name"] == "Test Artist"
        assert plan["subject"] == "Test Subject"
        assert plan["total_layers"] == 3
        assert len(plan["layers"]) == 3

    def test_all_plan_layer_fields_populated(self, planner_client: PlannerLLMClient) -> None:
        """Test that all PlanLayer fields are correctly populated."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": "Detailed description",
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test Layer",
                        "description": "Test layer description",
                        "colour_palette": ["#AABBCC"],
                        "stroke_types": ["line"],
                        "techniques": "Test techniques",
                        "shapes": "Test shapes",
                        "highlights": "Test highlights",
                    }
                ],
                "overall_notes": "Test notes",
            }
        )

        plan = planner_client._parse_plan_response(response)
        layer = plan["layers"][0]

        assert layer["layer_number"] == 1
        assert layer["name"] == "Test Layer"
        assert layer["description"] == "Test layer description"
        assert layer["colour_palette"] == ["#AABBCC"]
        assert layer["stroke_types"] == ["line"]
        assert layer["techniques"] == "Test techniques"
        assert layer["shapes"] == "Test shapes"
        assert layer["highlights"] == "Test highlights"

    def test_total_layers_matches_layer_count(self, planner_client: PlannerLLMClient) -> None:
        """Test that total_layers matches len(layers)."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 2,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Layer 1",
                        "description": "Description 1",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Tech 1",
                        "shapes": "Shapes 1",
                        "highlights": "Highlights 1",
                    },
                    {
                        "layer_number": 2,
                        "name": "Layer 2",
                        "description": "Description 2",
                        "colour_palette": ["#33FF57"],
                        "stroke_types": ["arc"],
                        "techniques": "Tech 2",
                        "shapes": "Shapes 2",
                        "highlights": "Highlights 2",
                    },
                ],
                "overall_notes": "Notes",
            }
        )

        plan = planner_client._parse_plan_response(response)

        assert plan["total_layers"] == len(plan["layers"])
        assert plan["total_layers"] == 2

    def test_json_wrapped_in_markdown_code_fences_cleaned(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that JSON wrapped in markdown code fences is cleaned and parsed."""
        plan_dict = {
            "artist_name": "Test Artist",
            "subject": "Test Subject",
            "expanded_subject": None,
            "total_layers": 1,
            "layers": [
                {
                    "layer_number": 1,
                    "name": "Test",
                    "description": "Test",
                    "colour_palette": ["#FF5733"],
                    "stroke_types": ["line"],
                    "techniques": "Test",
                    "shapes": "Test",
                    "highlights": "Test",
                }
            ],
            "overall_notes": "Notes",
        }
        response = f"```json\n{json.dumps(plan_dict)}\n```"

        plan = planner_client._parse_plan_response(response)

        assert plan["artist_name"] == "Test Artist"
        assert len(plan["layers"]) == 1

    def test_json_with_comments_cleaned(self, planner_client: PlannerLLMClient) -> None:
        """Test that JSON with // comments is cleaned and parsed."""
        response = """{
  // This is a comment
  "artist_name": "Test Artist",
  "subject": "Test Subject",
  "expanded_subject": null,
  "total_layers": 1,
  "layers": [
    {
      "layer_number": 1,  // Layer comment
      "name": "Test",
      "description": "Test",
      "colour_palette": ["#FF5733"],
      "stroke_types": ["line"],
      "techniques": "Test",
      "shapes": "Test",
      "highlights": "Test"
    }
  ],
  "overall_notes": "Notes"
}"""

        plan = planner_client._parse_plan_response(response)

        assert plan["artist_name"] == "Test Artist"


class TestResponseParsingValidationErrors:
    """Tests for response parsing validation errors."""

    def test_missing_layers_field_raises_value_error(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that missing layers field raises ValueError."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "total_layers": 1,
                "overall_notes": "Notes",
            }
        )

        with pytest.raises(ValueError, match="missing 'layers' field"):
            planner_client._parse_plan_response(response)

    def test_empty_layers_list_raises_value_error(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that empty layers list raises ValueError."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 0,
                "layers": [],
                "overall_notes": "Notes",
            }
        )

        with pytest.raises(ValueError, match="'layers' list cannot be empty"):
            planner_client._parse_plan_response(response)

    def test_layer_missing_required_field_raises_value_error(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that layer missing required field raises ValueError."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        # Missing "description" field
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                    }
                ],
                "overall_notes": "Notes",
            }
        )

        with pytest.raises(ValueError, match="missing required fields"):
            planner_client._parse_plan_response(response)

    def test_non_sequential_layer_numbers_raise_value_error(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that non-sequential layer_number values raise ValueError."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 2,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Layer 1",
                        "description": "Description 1",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Tech 1",
                        "shapes": "Shapes 1",
                        "highlights": "Highlights 1",
                    },
                    {
                        "layer_number": 3,  # Should be 2
                        "name": "Layer 3",
                        "description": "Description 3",
                        "colour_palette": ["#33FF57"],
                        "stroke_types": ["arc"],
                        "techniques": "Tech 3",
                        "shapes": "Shapes 3",
                        "highlights": "Highlights 3",
                    },
                ],
                "overall_notes": "Notes",
            }
        )

        with pytest.raises(ValueError, match="has layer_number 3, expected 2"):
            planner_client._parse_plan_response(response)

    def test_invalid_hex_color_raises_value_error(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that invalid hex colour in colour_palette raises ValueError."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        "description": "Test",
                        "colour_palette": ["INVALID"],  # Invalid hex color
                        "stroke_types": ["line"],
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                    }
                ],
                "overall_notes": "Notes",
            }
        )

        with pytest.raises(ValueError, match="invalid hex color"):
            planner_client._parse_plan_response(response)

    def test_invalid_stroke_type_raises_value_error(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that invalid stroke type in stroke_types raises ValueError."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        "description": "Test",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["invalid_stroke"],  # Invalid stroke type
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                    }
                ],
                "overall_notes": "Notes",
            }
        )

        with pytest.raises(ValueError, match="unsupported stroke type"):
            planner_client._parse_plan_response(response)

    def test_total_layers_mismatch_raises_value_error(
        self, planner_client: PlannerLLMClient
    ) -> None:
        """Test that total_layers mismatch with actual layer count raises ValueError."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 5,  # Mismatch: says 5 but only provides 1
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        "description": "Test",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                    }
                ],
                "overall_notes": "Notes",
            }
        )

        with pytest.raises(ValueError, match="does not match actual layer count"):
            planner_client._parse_plan_response(response)


class TestResponseParsingEdgeCases:
    """Tests for edge cases in response parsing."""

    def test_single_layer_plan_valid(self, planner_client: PlannerLLMClient) -> None:
        """Test that single-layer plan is valid."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Single Layer",
                        "description": "Only one layer",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Simple",
                        "shapes": "Basic",
                        "highlights": "Minimal",
                    }
                ],
                "overall_notes": "Single layer plan",
            }
        )

        plan = planner_client._parse_plan_response(response)

        assert plan["total_layers"] == 1
        assert len(plan["layers"]) == 1

    def test_large_plan_with_many_layers(self, planner_client: PlannerLLMClient) -> None:
        """Test that very large plan (10+ layers) parses fine."""
        layers = []
        for i in range(1, 15):
            layers.append(
                {
                    "layer_number": i,
                    "name": f"Layer {i}",
                    "description": f"Description {i}",
                    "colour_palette": [f"#FF{i:04X}"],
                    "stroke_types": ["line"],
                    "techniques": f"Tech {i}",
                    "shapes": f"Shapes {i}",
                    "highlights": f"Highlights {i}",
                }
            )

        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 14,
                "layers": layers,
                "overall_notes": "Large plan",
            }
        )

        plan = planner_client._parse_plan_response(response)

        assert plan["total_layers"] == 14
        assert len(plan["layers"]) == 14

    def test_extra_fields_in_response_tolerated(self, planner_client: PlannerLLMClient) -> None:
        """Test that extra fields in response are ignored/tolerated."""
        response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "extra_field": "This should be ignored",  # Extra field
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        "description": "Test",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                        "extra_layer_field": "Also ignored",  # Extra field
                    }
                ],
                "overall_notes": "Notes",
            }
        )

        # Should not raise, extra fields are tolerated
        plan = planner_client._parse_plan_response(response)

        assert plan["artist_name"] == "Test Artist"


class TestGeneratePlan:
    """Tests for generate_plan method."""

    def test_generate_plan_calls_vlm_client_query(
        self, planner_client: PlannerLLMClient, mock_vlm_client: Mock
    ) -> None:
        """Test that generate_plan calls VLMClient.query."""
        mock_vlm_client.query.return_value = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        "description": "Test",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                    }
                ],
                "overall_notes": "Notes",
            }
        )

        planner_client.generate_plan(
            artist_name="Test Artist",
            subject="Test Subject",
            expanded_subject=None,
            stroke_types=["line", "arc"],
        )

        mock_vlm_client.query.assert_called_once()

    def test_generate_plan_stores_raw_response(
        self, planner_client: PlannerLLMClient, mock_vlm_client: Mock
    ) -> None:
        """Test that generate_plan stores the raw response."""
        raw_response = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        "description": "Test",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                    }
                ],
                "overall_notes": "Notes",
            }
        )
        mock_vlm_client.query.return_value = raw_response

        planner_client.generate_plan(
            artist_name="Test Artist",
            subject="Test Subject",
            expanded_subject=None,
            stroke_types=["line"],
        )

        assert planner_client.last_raw_response == raw_response

    def test_generate_plan_stores_parsed_response(
        self, planner_client: PlannerLLMClient, mock_vlm_client: Mock
    ) -> None:
        """Test that generate_plan stores the parsed response."""
        mock_vlm_client.query.return_value = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        "description": "Test",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                    }
                ],
                "overall_notes": "Notes",
            }
        )

        plan = planner_client.generate_plan(
            artist_name="Test Artist",
            subject="Test Subject",
            expanded_subject=None,
            stroke_types=["line"],
        )

        assert planner_client.last_parsed_response == plan

    def test_generate_plan_records_interaction_history(
        self, planner_client: PlannerLLMClient, mock_vlm_client: Mock
    ) -> None:
        """Test that generate_plan records interaction in history."""
        mock_vlm_client.query.return_value = json.dumps(
            {
                "artist_name": "Test Artist",
                "subject": "Test Subject",
                "expanded_subject": None,
                "total_layers": 1,
                "layers": [
                    {
                        "layer_number": 1,
                        "name": "Test",
                        "description": "Test",
                        "colour_palette": ["#FF5733"],
                        "stroke_types": ["line"],
                        "techniques": "Test",
                        "shapes": "Test",
                        "highlights": "Test",
                    }
                ],
                "overall_notes": "Notes",
            }
        )

        planner_client.generate_plan(
            artist_name="Test Artist",
            subject="Test Subject",
            expanded_subject=None,
            stroke_types=["line"],
        )

        history = planner_client.get_interaction_history()
        assert len(history) == 1
        assert history[0]["artist_name"] == "Test Artist"
        assert history[0]["subject"] == "Test Subject"
        assert history[0]["layer_count"] == 1
