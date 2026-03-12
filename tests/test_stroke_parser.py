"""Unit tests for StrokeParser."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.stroke_parser import StrokeParser

# ============================================================================
# Fixtures / helpers
# ============================================================================

ALL_TEN_STROKES = [
    {
        "type": "line",
        "start_x": 10,
        "start_y": 20,
        "end_x": 100,
        "end_y": 200,
        "color_hex": "#FF0000",
        "thickness": 2,
        "opacity": 0.8,
    },
    {
        "type": "arc",
        "arc_bbox": [50, 50, 250, 250],
        "arc_start_angle": 0,
        "arc_end_angle": 180,
        "color_hex": "#00FF00",
        "thickness": 3,
        "opacity": 0.9,
    },
    {
        "type": "polyline",
        "points": [[100, 100], [150, 200], [200, 150]],
        "color_hex": "#0000FF",
        "thickness": 4,
        "opacity": 0.7,
    },
    {
        "type": "circle",
        "center_x": 300,
        "center_y": 300,
        "radius": 50,
        "fill": True,
        "color_hex": "#FFFF00",
        "thickness": 2,
        "opacity": 0.6,
    },
    {
        "type": "splatter",
        "center_x": 200,
        "center_y": 150,
        "splatter_radius": 30,
        "splatter_count": 15,
        "dot_size_min": 2,
        "dot_size_max": 6,
        "color_hex": "#8B4513",
        "thickness": 1,
        "opacity": 0.5,
    },
    {
        "type": "dry-brush",
        "points": [[100, 100], [300, 200], [500, 150]],
        "brush_width": 30,
        "bristle_count": 8,
        "gap_probability": 0.3,
        "color_hex": "#A0522D",
        "thickness": 20,
        "opacity": 0.8,
    },
    {
        "type": "chalk",
        "points": [[150, 200], [350, 180], [450, 250]],
        "chalk_width": 20,
        "grain_density": 4,
        "color_hex": "#D2691E",
        "thickness": 1,
        "opacity": 0.7,
    },
    {
        "type": "wet-brush",
        "points": [[100, 200], [300, 180], [500, 220]],
        "softness": 12,
        "flow": 0.7,
        "color_hex": "#4477AA",
        "thickness": 14,
        "opacity": 0.75,
    },
    {
        "type": "burn",
        "center_x": 400,
        "center_y": 300,
        "radius": 80,
        "intensity": 0.6,
        "color_hex": "#000000",
        "thickness": 1,
        "opacity": 1.0,
    },
    {
        "type": "dodge",
        "center_x": 400,
        "center_y": 300,
        "radius": 80,
        "intensity": 0.6,
        "color_hex": "#FFFFFF",
        "thickness": 1,
        "opacity": 1.0,
    },
]

_BATCH_JSON = json.dumps(
    {
        "strokes": ALL_TEN_STROKES,
        "updated_strategy": None,
        "batch_reasoning": "All ten stroke types test",
    }
)

_LEGACY_SINGLE_STROKE_JSON = json.dumps(
    {
        "stroke": {
            "type": "line",
            "start_x": 10,
            "start_y": 20,
            "end_x": 100,
            "end_y": 200,
            "color_hex": "#FF0000",
            "thickness": 2,
            "opacity": 0.8,
            "reasoning": "Legacy single stroke test",
        }
    }
)

_MISSING_KEYS_JSON = json.dumps({"updated_strategy": None, "batch_reasoning": "oops"})


# ============================================================================
# Tests
# ============================================================================


def test_parse_all_ten_stroke_types() -> None:
    """Valid batch JSON with all ten stroke types returns 10 strokes, each with correct type.

    Verifies that StrokeParser.parse correctly handles every supported stroke
    type end-to-end and returns exactly the number of strokes supplied.
    """
    parser = StrokeParser()
    result = parser.parse(_BATCH_JSON)

    assert len(result["strokes"]) == 10, (
        f"Expected 10 strokes, got {len(result['strokes'])}"
    )

    expected_types = [s["type"] for s in ALL_TEN_STROKES]
    actual_types = [s["type"] for s in result["strokes"]]
    assert actual_types == expected_types, (
        f"Stroke type list mismatch.\nExpected: {expected_types}\nActual:   {actual_types}"
    )


def test_parse_batch_reasoning_preserved() -> None:
    """batch_reasoning from the JSON response is preserved in the returned StrokeVLMResponse."""
    parser = StrokeParser()
    result = parser.parse(_BATCH_JSON)

    assert result["batch_reasoning"] == "All ten stroke types test"


def test_parse_legacy_single_stroke_format() -> None:
    """Old single-stroke format (``"stroke"`` key) is backward-compatible.

    Verifies that a response using the legacy ``"stroke"`` key is converted to
    a list containing exactly one stroke.
    """
    parser = StrokeParser()
    result = parser.parse(_LEGACY_SINGLE_STROKE_JSON)

    assert len(result["strokes"]) == 1, (
        f"Expected 1 stroke from legacy format, got {len(result['strokes'])}"
    )
    assert result["strokes"][0]["type"] == "line"


def test_parse_skips_stroke_missing_required_field() -> None:
    """A stroke missing a required field is skipped; valid strokes are still returned.

    The bad stroke (``arc`` missing ``arc_start_angle``) should be omitted from
    the result while the valid line stroke is returned.
    """
    bad_stroke = {
        "type": "arc",
        "arc_bbox": [50, 50, 250, 250],
        # arc_start_angle deliberately missing
        "arc_end_angle": 180,
        "color_hex": "#00FF00",
        "thickness": 3,
        "opacity": 0.9,
    }
    good_stroke = {
        "type": "line",
        "start_x": 0,
        "start_y": 0,
        "end_x": 100,
        "end_y": 100,
        "color_hex": "#AABBCC",
        "thickness": 1,
        "opacity": 1.0,
    }
    payload = json.dumps(
        {
            "strokes": [bad_stroke, good_stroke],
            "updated_strategy": None,
            "batch_reasoning": "skip test",
        }
    )

    parser = StrokeParser()
    result = parser.parse(payload)

    assert len(result["strokes"]) == 1, (
        f"Expected 1 valid stroke (bad one skipped), got {len(result['strokes'])}"
    )
    assert result["strokes"][0]["type"] == "line"


def test_parse_raises_value_error_for_missing_strokes_key() -> None:
    """JSON missing both ``"strokes"`` and ``"stroke"`` keys raises ValueError."""
    parser = StrokeParser()
    with pytest.raises(ValueError, match="missing both"):
        parser.parse(_MISSING_KEYS_JSON)


def test_parse_handles_markdown_fenced_json() -> None:
    """JSON wrapped in \\`\\`\\`json … \\`\\`\\` markdown fences is parsed correctly.

    Verifies that ``clean_and_parse_json`` (called internally) strips fences
    before parsing, so VLMs that wrap their output in code blocks are handled
    gracefully.
    """
    inner = {
        "strokes": [
            {
                "type": "circle",
                "center_x": 100,
                "center_y": 100,
                "radius": 40,
                "fill": False,
                "color_hex": "#123456",
                "thickness": 2,
                "opacity": 0.5,
            }
        ],
        "updated_strategy": None,
        "batch_reasoning": "fenced json test",
    }
    fenced = f"```json\n{json.dumps(inner)}\n```"

    parser = StrokeParser()
    result = parser.parse(fenced)

    assert len(result["strokes"]) == 1
    assert result["strokes"][0]["type"] == "circle"


def test_parse_layer_complete_forwarded() -> None:
    """``layer_complete`` field from the VLM response is forwarded to the returned dict."""
    payload = json.dumps(
        {
            "strokes": [],
            "updated_strategy": None,
            "batch_reasoning": "layer complete test",
            "layer_complete": True,
        }
    )
    parser = StrokeParser()
    result = parser.parse(payload)

    assert result.get("layer_complete") is True


def test_parse_type_specific_fields_line() -> None:
    """Line stroke fields are correctly typed after parsing."""
    parser = StrokeParser()
    result = parser.parse(_BATCH_JSON)
    line = next(s for s in result["strokes"] if s["type"] == "line")

    assert isinstance(line["start_x"], int)
    assert isinstance(line["start_y"], int)
    assert isinstance(line["end_x"], int)
    assert isinstance(line["end_y"], int)


def test_parse_type_specific_fields_burn_dodge() -> None:
    """Burn and dodge strokes both have ``intensity`` parsed as float."""
    parser = StrokeParser()
    result = parser.parse(_BATCH_JSON)

    burn = next(s for s in result["strokes"] if s["type"] == "burn")
    dodge = next(s for s in result["strokes"] if s["type"] == "dodge")

    assert isinstance(burn["intensity"], float)
    assert isinstance(dodge["intensity"], float)


def test_stroke_parser_importable_from_services() -> None:
    """StrokeParser is importable from the ``services`` package."""
    from services import StrokeParser as SP  # noqa: F401

    assert SP is StrokeParser
