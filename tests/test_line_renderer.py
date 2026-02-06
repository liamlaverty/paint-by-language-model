"""Unit tests for LineRenderer."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import LineRenderer, StrokeRendererFactory  # noqa: E402


def test_factory_returns_line_renderer() -> None:
    """Test that factory correctly returns LineRenderer for 'line' type."""
    renderer = StrokeRendererFactory.get_renderer("line")
    assert isinstance(renderer, LineRenderer)
    print("✓ Factory returns LineRenderer for 'line' type")


def test_validation_valid_stroke() -> None:
    """Test validation passes for valid line stroke."""
    renderer = LineRenderer()
    stroke = {
        "type": "line",
        "start_x": 10,
        "start_y": 20,
        "end_x": 100,
        "end_y": 200,
        "color_hex": "#FF5733",
        "thickness": 3,
        "opacity": 0.8,
    }
    canvas_size = (800, 600)

    try:
        renderer.validate(stroke, canvas_size)  # type: ignore
        print("✓ Validation passes for valid stroke")
    except ValueError as e:
        print(f"✗ Validation failed unexpectedly: {e}")


def test_validation_8digit_hex() -> None:
    """Test validation accepts 8-digit hex colors."""
    renderer = LineRenderer()
    stroke = {
        "type": "line",
        "start_x": 10,
        "start_y": 20,
        "end_x": 100,
        "end_y": 200,
        "color_hex": "#FF5733CC",  # 8-digit with alpha
        "thickness": 3,
        "opacity": 0.8,
    }
    canvas_size = (800, 600)

    try:
        renderer.validate(stroke, canvas_size)  # type: ignore
        print("✓ Validation accepts 8-digit hex colors (#RRGGBBAA)")
    except ValueError as e:
        print(f"✗ Validation rejected 8-digit hex: {e}")


def test_validation_missing_field() -> None:
    """Test validation fails for missing required field."""
    renderer = LineRenderer()
    stroke = {
        "type": "line",
        "start_x": 10,
        "start_y": 20,
        "end_x": 100,
        # Missing end_y
        "color_hex": "#FF5733",
        "thickness": 3,
        "opacity": 0.8,
    }
    canvas_size = (800, 600)

    try:
        renderer.validate(stroke, canvas_size)  # type: ignore
        print("✗ Validation should have failed for missing field")
    except ValueError as e:
        if "end_y" in str(e):
            print(f"✓ Validation correctly rejects missing field: {e}")
        else:
            print(f"⚠ Validation failed but wrong message: {e}")


def test_validation_out_of_bounds() -> None:
    """Test validation fails for coordinates out of bounds."""
    renderer = LineRenderer()
    stroke = {
        "type": "line",
        "start_x": 10,
        "start_y": 20,
        "end_x": 900,  # Out of bounds for 800x600 canvas
        "end_y": 200,
        "color_hex": "#FF5733",
        "thickness": 3,
        "opacity": 0.8,
    }
    canvas_size = (800, 600)

    try:
        renderer.validate(stroke, canvas_size)  # type: ignore
        print("✗ Validation should have failed for out of bounds coordinate")
    except ValueError as e:
        if "out of bounds" in str(e):
            print(f"✓ Validation correctly rejects out of bounds: {e}")
        else:
            print(f"⚠ Validation failed but wrong message: {e}")


def test_validation_invalid_hex() -> None:
    """Test validation fails for invalid hex color."""
    renderer = LineRenderer()
    stroke = {
        "type": "line",
        "start_x": 10,
        "start_y": 20,
        "end_x": 100,
        "end_y": 200,
        "color_hex": "#GGGGGG",  # Invalid hex
        "thickness": 3,
        "opacity": 0.8,
    }
    canvas_size = (800, 600)

    try:
        renderer.validate(stroke, canvas_size)  # type: ignore
        print("✗ Validation should have failed for invalid hex color")
    except ValueError as e:
        if "hex color" in str(e).lower():
            print(f"✓ Validation correctly rejects invalid hex: {e}")
        else:
            print(f"⚠ Validation failed but wrong message: {e}")


def test_render_6digit_hex() -> None:
    """Test rendering with 6-digit hex color."""
    renderer = LineRenderer()
    image = Image.new("RGB", (800, 600), "#FFFFFF")
    draw = ImageDraw.Draw(image, "RGBA")

    stroke = {
        "type": "line",
        "start_x": 100,
        "start_y": 100,
        "end_x": 200,
        "end_y": 200,
        "color_hex": "#FF0000",  # Red
        "thickness": 5,
        "opacity": 0.8,
    }

    try:
        renderer.render(stroke, draw)  # type: ignore
        print("✓ Rendering works with 6-digit hex color")
    except Exception as e:
        print(f"✗ Rendering failed: {e}")


def test_render_8digit_hex() -> None:
    """Test rendering with 8-digit hex color (with alpha)."""
    renderer = LineRenderer()
    image = Image.new("RGB", (800, 600), "#FFFFFF")
    draw = ImageDraw.Draw(image, "RGBA")

    stroke = {
        "type": "line",
        "start_x": 100,
        "start_y": 100,
        "end_x": 200,
        "end_y": 200,
        "color_hex": "#FF0000CC",  # Red with alpha
        "thickness": 5,
        "opacity": 0.8,  # Should be ignored when 8-digit hex provided
    }

    try:
        renderer.render(stroke, draw)  # type: ignore
        print("✓ Rendering works with 8-digit hex color (RGBA)")
    except Exception as e:
        print(f"✗ Rendering failed: {e}")


if __name__ == "__main__":
    print("=== LineRenderer Tests ===\n")

    print("Factory Registration:")
    test_factory_returns_line_renderer()

    print("\nValidation Tests:")
    test_validation_valid_stroke()
    test_validation_8digit_hex()
    test_validation_missing_field()
    test_validation_out_of_bounds()
    test_validation_invalid_hex()

    print("\nRendering Tests:")
    test_render_6digit_hex()
    test_render_8digit_hex()

    print("\n=== All Tests Complete ===")
