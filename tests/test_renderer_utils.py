"""Unit tests for renderer utility functions."""

import sys
from pathlib import Path

import pytest

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from services.renderers.renderer_utils import (  # noqa: E402
    hex_to_rgb,
    hex_to_rgba,
    stroke_color_to_rgba,
    validate_color_hex,
    validate_common_stroke_fields,
    validate_opacity,
    validate_thickness,
)


def test_hex_to_rgb() -> None:
    """Test conversion of 6-digit hex to RGB."""
    assert hex_to_rgb("#FF5733") == (255, 87, 51)
    assert hex_to_rgb("#000000") == (0, 0, 0)
    assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
    print("✓ hex_to_rgb works correctly")


def test_hex_to_rgba() -> None:
    """Test conversion of 8-digit hex to RGBA."""
    assert hex_to_rgba("#FF5733CC") == (255, 87, 51, 204)
    assert hex_to_rgba("#000000FF") == (0, 0, 0, 255)
    assert hex_to_rgba("#FFFFFF00") == (255, 255, 255, 0)
    print("✓ hex_to_rgba works correctly")


def test_stroke_color_to_rgba_6digit() -> None:
    """Test color conversion with 6-digit hex and opacity."""
    # Full opacity
    result = stroke_color_to_rgba("#FF5733", 1.0)
    assert result == (255, 87, 51, 255)

    # Half opacity
    result = stroke_color_to_rgba("#FF5733", 0.5)
    assert result == (255, 87, 51, 127)

    # Zero opacity
    result = stroke_color_to_rgba("#FF5733", 0.0)
    assert result == (255, 87, 51, 0)

    print("✓ stroke_color_to_rgba works with 6-digit hex")


def test_stroke_color_to_rgba_8digit() -> None:
    """Test color conversion with 8-digit hex (opacity in hex overrides opacity param)."""
    # 8-digit hex alpha channel is used, opacity parameter is ignored
    result = stroke_color_to_rgba("#FF5733CC", 1.0)
    assert result == (255, 87, 51, 204)

    result = stroke_color_to_rgba("#FF5733CC", 0.5)
    assert result == (255, 87, 51, 204)  # Still uses CC (204) from hex

    print("✓ stroke_color_to_rgba works with 8-digit hex")


def test_validate_color_hex_valid() -> None:
    """Test validation of valid hex colors."""
    validate_color_hex("#FF5733")
    validate_color_hex("#ff5733")  # lowercase
    validate_color_hex("#FF5733CC")  # 8-digit
    validate_color_hex("#00000000")  # all zeros
    print("✓ validate_color_hex accepts valid colors")


def test_validate_color_hex_invalid() -> None:
    """Test validation rejects invalid hex colors."""
    with pytest.raises(ValueError, match="Invalid hex color format"):
        validate_color_hex("FF5733")  # Missing #

    with pytest.raises(ValueError, match="Invalid hex color format"):
        validate_color_hex("#FF57")  # Too short

    with pytest.raises(ValueError, match="Invalid hex color format"):
        validate_color_hex("#FF5733C")  # 7 digits (invalid)

    with pytest.raises(ValueError, match="Invalid hex color format"):
        validate_color_hex("#GGGGGG")  # Invalid hex characters

    print("✓ validate_color_hex rejects invalid colors")


def test_validate_thickness_valid() -> None:
    """Test validation of valid thickness values."""
    validate_thickness(1)
    validate_thickness(5)
    validate_thickness(10)
    print("✓ validate_thickness accepts valid values")


def test_validate_thickness_invalid() -> None:
    """Test validation rejects invalid thickness values."""
    with pytest.raises(ValueError, match="thickness must be an integer"):
        validate_thickness(5.5)  # type: ignore

    with pytest.raises(ValueError, match="out of range"):
        validate_thickness(0)

    with pytest.raises(ValueError, match="out of range"):
        validate_thickness(110)

    print("✓ validate_thickness rejects invalid values")


def test_validate_opacity_valid() -> None:
    """Test validation of valid opacity values."""
    validate_opacity(0.1)
    validate_opacity(0.5)
    validate_opacity(1.0)
    validate_opacity(1)  # Integer is also valid
    print("✓ validate_opacity accepts valid values")


def test_validate_opacity_invalid() -> None:
    """Test validation rejects invalid opacity values."""
    with pytest.raises(ValueError, match="opacity must be a number"):
        validate_opacity("0.5")  # type: ignore

    with pytest.raises(ValueError, match="out of range"):
        validate_opacity(0.05)

    with pytest.raises(ValueError, match="out of range"):
        validate_opacity(1.1)

    print("✓ validate_opacity rejects invalid values")


def test_validate_common_stroke_fields_valid() -> None:
    """Test validation of valid common stroke fields."""
    stroke = {
        "type": "line",
        "color_hex": "#FF5733",
        "thickness": 5,
        "opacity": 0.8,
        "start_x": 0,
        "start_y": 0,
        "end_x": 100,
        "end_y": 100,
        "reasoning": "Test",
    }
    validate_common_stroke_fields(stroke)
    print("✓ validate_common_stroke_fields accepts valid stroke")


def test_validate_common_stroke_fields_invalid() -> None:
    """Test validation rejects invalid common stroke fields."""
    # Invalid color
    stroke = {
        "type": "line",
        "color_hex": "INVALID",
        "thickness": 5,
        "opacity": 0.8,
        "start_x": 0,
        "start_y": 0,
        "end_x": 100,
        "end_y": 100,
        "reasoning": "Test",
    }
    with pytest.raises(ValueError, match="Invalid hex color format"):
        validate_common_stroke_fields(stroke)

    # Invalid thickness
    stroke["color_hex"] = "#FF5733"
    stroke["thickness"] = 101  # Exceeds MAX_STROKE_THICKNESS (100)
    with pytest.raises(ValueError, match="out of range"):
        validate_common_stroke_fields(stroke)

    # Invalid opacity
    stroke["thickness"] = 5
    stroke["opacity"] = 2.0
    with pytest.raises(ValueError, match="out of range"):
        validate_common_stroke_fields(stroke)

    print("✓ validate_common_stroke_fields rejects invalid stroke")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
