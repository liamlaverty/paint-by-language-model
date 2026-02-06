"""Unit tests for PolylineRenderer."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

import pytest  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import PolylineRenderer, StrokeRendererFactory  # noqa: E402


def test_factory_returns_polyline_renderer() -> None:
    """Test that factory correctly returns PolylineRenderer for 'polyline' type."""
    renderer = StrokeRendererFactory.get_renderer("polyline")
    assert isinstance(renderer, PolylineRenderer)
    print("✓ Factory returns PolylineRenderer for 'polyline' type")


def test_validation_valid_polyline() -> None:
    """Test validation passes for valid polyline stroke."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[10, 20], [50, 80], [100, 60], [150, 100]],
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    try:
        renderer.validate(stroke, canvas_size)  # type: ignore
        print("✓ Validation passes for valid polyline")
    except ValueError as e:
        pytest.fail(f"Validation failed unexpectedly: {e}")


def test_validation_minimum_points() -> None:
    """Test validation passes for minimum 2 points."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[0, 0], [100, 100]],
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    try:
        renderer.validate(stroke, canvas_size)  # type: ignore
        print("✓ Validation passes for minimum 2 points")
    except ValueError as e:
        pytest.fail(f"Validation failed for minimum points: {e}")


def test_validation_maximum_points() -> None:
    """Test validation passes for maximum 50 points."""
    renderer = PolylineRenderer()
    # Create polyline with exactly 50 points
    points = [[i * 10, i * 5] for i in range(50)]
    stroke = {
        "type": "polyline",
        "points": points,
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    try:
        renderer.validate(stroke, canvas_size)  # type: ignore
        print("✓ Validation passes for maximum 50 points")
    except ValueError as e:
        pytest.fail(f"Validation failed for maximum points: {e}")


def test_validation_missing_points_field() -> None:
    """Test validation fails for missing points field."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        # Missing points field
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="missing required field: points"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects missing points field")


def test_validation_too_few_points() -> None:
    """Test validation fails for fewer than 2 points."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[50, 50]],  # Only 1 point
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="must have at least 2 points"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects single point")


def test_validation_too_many_points() -> None:
    """Test validation fails for more than 50 points."""
    renderer = PolylineRenderer()
    # Create polyline with 51 points
    points = [[i * 10, i * 5] for i in range(51)]
    stroke = {
        "type": "polyline",
        "points": points,
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="cannot have more than 50 points"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects more than 50 points")


def test_validation_empty_points() -> None:
    """Test validation fails for empty points list."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [],  # Empty list
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="must have at least 2 points"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects empty points list")


def test_validation_out_of_bounds_point() -> None:
    """Test validation fails for point coordinates out of bounds."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[10, 20], [50, 80], [900, 60]],  # x=900 out of bounds for 800x600
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="out of bounds"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects out-of-bounds points")


def test_validation_invalid_point_format() -> None:
    """Test validation fails for invalid point format."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[10, 20], [50]],  # Second point has only 1 coordinate
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="must have exactly 2 coordinates"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects invalid point format")


def test_validation_non_integer_coordinates() -> None:
    """Test validation fails for non-integer coordinates."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[10, 20], [50.5, 80]],  # Float coordinate
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="must be an integer"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects non-integer coordinates")


def test_validation_invalid_hex() -> None:
    """Test validation fails for invalid hex color."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[10, 20], [50, 80]],
        "color_hex": "invalid",  # Invalid hex format
        "thickness": 2,
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="Invalid hex color"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects invalid hex color")


def test_validation_invalid_thickness() -> None:
    """Test validation fails for invalid thickness."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[10, 20], [50, 80]],
        "color_hex": "#228B22",
        "thickness": 100,  # Exceeds max thickness of 50
        "opacity": 0.7,
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="thickness .* out of range"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects invalid thickness")


def test_validation_invalid_opacity() -> None:
    """Test validation fails for invalid opacity."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[10, 20], [50, 80]],
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 1.5,  # Exceeds max opacity of 1.0
    }
    canvas_size = (800, 600)

    with pytest.raises(ValueError, match="opacity .* out of range"):
        renderer.validate(stroke, canvas_size)  # type: ignore
    print("✓ Validation correctly rejects invalid opacity")


def test_render_simple_polyline() -> None:
    """Test rendering a simple polyline."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[10, 20], [50, 80], [100, 60], [150, 100]],
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }

    # Create test canvas
    image = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        renderer.render(stroke, draw)  # type: ignore
        print("✓ Successfully rendered polyline")
    except Exception as e:
        pytest.fail(f"Rendering failed: {e}")


def test_render_two_point_polyline() -> None:
    """Test rendering a two-point polyline (equivalent to a line)."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [[0, 0], [100, 100]],
        "color_hex": "#FF0000",
        "thickness": 3,
        "opacity": 1.0,
    }

    # Create test canvas
    image = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        renderer.render(stroke, draw)  # type: ignore
        print("✓ Successfully rendered two-point polyline")
    except Exception as e:
        pytest.fail(f"Rendering failed: {e}")


def test_render_complex_polyline() -> None:
    """Test rendering a complex polyline with many points."""
    renderer = PolylineRenderer()
    # Create a zigzag pattern
    points = [[i * 10, 50 + (i % 2) * 30] for i in range(10)]
    stroke = {
        "type": "polyline",
        "points": points,
        "color_hex": "#0000FF",
        "thickness": 1,
        "opacity": 0.5,
    }

    # Create test canvas
    image = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        renderer.render(stroke, draw)  # type: ignore
        print("✓ Successfully rendered complex polyline")
    except Exception as e:
        pytest.fail(f"Rendering failed: {e}")


def test_render_with_tuples() -> None:
    """Test rendering works with tuple points (not just lists)."""
    renderer = PolylineRenderer()
    stroke = {
        "type": "polyline",
        "points": [(10, 20), (50, 80), (100, 60)],  # Tuples instead of lists
        "color_hex": "#228B22",
        "thickness": 2,
        "opacity": 0.7,
    }

    # Create test canvas
    image = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        renderer.render(stroke, draw)  # type: ignore
        print("✓ Successfully rendered polyline with tuple points")
    except Exception as e:
        pytest.fail(f"Rendering failed: {e}")


if __name__ == "__main__":
    # Run tests manually
    test_factory_returns_polyline_renderer()
    test_validation_valid_polyline()
    test_validation_minimum_points()
    test_validation_maximum_points()
    test_validation_missing_points_field()
    test_validation_too_few_points()
    test_validation_too_many_points()
    test_validation_empty_points()
    test_validation_out_of_bounds_point()
    test_validation_invalid_point_format()
    test_validation_non_integer_coordinates()
    test_validation_invalid_hex()
    test_validation_invalid_thickness()
    test_validation_invalid_opacity()
    test_render_simple_polyline()
    test_render_two_point_polyline()
    test_render_complex_polyline()
    test_render_with_tuples()
    print("\n✅ All PolylineRenderer tests passed!")
