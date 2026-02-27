"""Tests for Phase 8 data models (PaintingPlan and EvaluationResult extensions)."""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from models.evaluation_result import EvaluationResult
from models.painting_plan import PaintingPlan, PlanLayer


class TestPlanLayer:
    """Tests for PlanLayer TypedDict."""

    def test_plan_layer_with_all_required_fields(self) -> None:
        """Test that PlanLayer can be constructed with all required fields."""
        layer: PlanLayer = {
            "layer_number": 1,
            "name": "Test Layer",
            "description": "Test description",
            "colour_palette": ["#FF0000", "#00FF00"],
            "stroke_types": ["line", "arc"],
            "techniques": "Test techniques",
            "shapes": "Test shapes",
            "highlights": "Test highlights",
        }

        assert layer["layer_number"] == 1
        assert layer["name"] == "Test Layer"
        assert len(layer["colour_palette"]) == 2
        assert len(layer["stroke_types"]) == 2


class TestPaintingPlan:
    """Tests for PaintingPlan TypedDict."""

    def test_painting_plan_with_all_required_fields(self) -> None:
        """Test that PaintingPlan can be constructed with all required fields."""
        plan: PaintingPlan = {
            "artist_name": "Test Artist",
            "subject": "Test Subject",
            "expanded_subject": None,
            "total_layers": 2,
            "layers": [
                {
                    "layer_number": 1,
                    "name": "Layer 1",
                    "description": "First layer",
                    "colour_palette": ["#FF0000"],
                    "stroke_types": ["line"],
                    "techniques": "Tech 1",
                    "shapes": "Shapes 1",
                    "highlights": "Highlights 1",
                },
                {
                    "layer_number": 2,
                    "name": "Layer 2",
                    "description": "Second layer",
                    "colour_palette": ["#00FF00"],
                    "stroke_types": ["arc"],
                    "techniques": "Tech 2",
                    "shapes": "Shapes 2",
                    "highlights": "Highlights 2",
                },
            ],
            "overall_notes": "Test notes",
        }

        assert plan["artist_name"] == "Test Artist"
        assert plan["total_layers"] == 2
        assert len(plan["layers"]) == 2

    def test_painting_plan_with_expanded_subject_none(self) -> None:
        """Test that PaintingPlan with expanded_subject: None is valid."""
        plan: PaintingPlan = {
            "artist_name": "Test Artist",
            "subject": "Test Subject",
            "expanded_subject": None,  # Explicitly None
            "total_layers": 1,
            "layers": [
                {
                    "layer_number": 1,
                    "name": "Only Layer",
                    "description": "Single layer",
                    "colour_palette": ["#FF0000"],
                    "stroke_types": ["line"],
                    "techniques": "Tech",
                    "shapes": "Shapes",
                    "highlights": "Highlights",
                }
            ],
            "overall_notes": "Notes",
        }

        assert plan["expanded_subject"] is None

    def test_painting_plan_with_expanded_subject_string(self) -> None:
        """Test that PaintingPlan with expanded_subject as string is valid."""
        expanded = "A detailed description of the painting"
        plan: PaintingPlan = {
            "artist_name": "Test Artist",
            "subject": "Test Subject",
            "expanded_subject": expanded,
            "total_layers": 1,
            "layers": [
                {
                    "layer_number": 1,
                    "name": "Layer",
                    "description": "Description",
                    "colour_palette": ["#FF0000"],
                    "stroke_types": ["line"],
                    "techniques": "Tech",
                    "shapes": "Shapes",
                    "highlights": "Highlights",
                }
            ],
            "overall_notes": "Notes",
        }

        assert plan["expanded_subject"] == expanded


class TestEvaluationResult:
    """Tests for EvaluationResult with optional layer fields."""

    def test_evaluation_result_with_layer_number(self) -> None:
        """Test that EvaluationResult with optional layer_number field works."""
        result: EvaluationResult = {
            "score": 75.0,
            "feedback": "Good progress",
            "strengths": "Color is good",
            "suggestions": "Add more detail",
            "timestamp": "2026-01-01T00:00:00",
            "iteration": 10,
            "layer_number": 2,
        }

        assert result["layer_number"] == 2

    def test_evaluation_result_without_layer_fields(self) -> None:
        """Test that EvaluationResult without layer_complete field works (backward compat)."""
        result: EvaluationResult = {
            "score": 65.0,
            "feedback": "Making progress",
            "strengths": "Good technique",
            "suggestions": "Continue",
            "timestamp": "2026-01-01T00:00:00",
            "iteration": 5,
        }

        assert result["score"] == 65.0
        assert "layer_number" not in result
        assert "layer_complete" not in result

    def test_evaluation_result_with_layer_number_only(self) -> None:
        """Test that EvaluationResult with layer_number but no layer_complete works."""
        result: EvaluationResult = {
            "score": 50.0,
            "feedback": "Needs work",
            "strengths": "Starting",
            "suggestions": "Keep going",
            "timestamp": "2026-01-01T00:00:00",
            "iteration": 3,
            "layer_number": 1,
        }

        assert result["layer_number"] == 1


class TestStrokeVLMResponseModel:
    """Tests for StrokeVLMResponse TypedDict with optional layer_complete field."""

    def test_stroke_vlm_response_with_layer_complete(self) -> None:
        """Test that StrokeVLMResponse can be constructed with layer_complete: True."""
        from models.stroke_vlm_response import StrokeVLMResponse

        response: StrokeVLMResponse = {
            "strokes": [],
            "updated_strategy": None,
            "batch_reasoning": "Test reasoning",
            "layer_complete": True,
        }

        assert response["layer_complete"] is True
        assert "layer_complete" in response

    def test_stroke_vlm_response_without_layer_complete(self) -> None:
        """Test that StrokeVLMResponse can be constructed without layer_complete."""
        from models.stroke_vlm_response import StrokeVLMResponse

        response: StrokeVLMResponse = {
            "strokes": [],
            "updated_strategy": None,
            "batch_reasoning": "Test reasoning",
        }

        assert "layer_complete" not in response
