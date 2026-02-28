"""Comprehensive tests for ChalkRenderer implementation."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import ChalkRenderer, StrokeRendererFactory  # noqa: E402


def test_factory_registration() -> None:
    """Test that ChalkRenderer is registered in factory."""
    print("\n=== Test: Factory Registration ===")
    renderer = StrokeRendererFactory.get_renderer("chalk")
    assert isinstance(renderer, ChalkRenderer)
    print("✓ Factory returns ChalkRenderer for 'chalk' type")


def test_valid_chalk_stroke() -> None:
    """Test validation passes with all valid fields."""
    print("\n=== Test: Valid Chalk Stroke ===")
    renderer = ChalkRenderer()
    canvas_size = (800, 600)

    stroke: Stroke = {
        "type": "chalk",
        "points": [[100, 100], [200, 200], [300, 150]],
        "chalk_width": 20,
        "grain_density": 4,
        "color_hex": "#FFFFFF",
        "thickness": 5,
        "opacity": 0.8,
        "reasoning": "Valid chalk stroke",
    }

    renderer.validate(stroke, canvas_size)
    print("✓ Valid chalk stroke passed validation")


def test_missing_required_fields() -> None:
    """Test that validation raises ValueError for missing required fields."""
    print("\n=== Test: Missing Required Fields ===")
    renderer = ChalkRenderer()
    canvas_size = (800, 600)

    # Missing points
    try:
        stroke: Stroke = {
            "type": "chalk",
            "chalk_width": 20,
            "grain_density": 4,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Missing points",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing points"
    except ValueError as e:
        print(f"✓ Caught expected error for missing points: {e}")

    # Missing chalk_width
    try:
        stroke = {
            "type": "chalk",
            "points": [[100, 100], [200, 200]],
            "grain_density": 4,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Missing chalk_width",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing chalk_width"
    except ValueError as e:
        print(f"✓ Caught expected error for missing chalk_width: {e}")

    # Missing grain_density
    try:
        stroke = {
            "type": "chalk",
            "points": [[100, 100], [200, 200]],
            "chalk_width": 20,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Missing grain_density",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing grain_density"
    except ValueError as e:
        print(f"✓ Caught expected error for missing grain_density: {e}")


def test_chalk_width_out_of_range() -> None:
    """Test that validation raises ValueError for chalk_width out of range."""
    print("\n=== Test: Chalk Width Out of Range ===")
    renderer = ChalkRenderer()
    canvas_size = (800, 600)

    # Below minimum
    try:
        stroke: Stroke = {
            "type": "chalk",
            "points": [[100, 100], [200, 200]],
            "chalk_width": 1,  # MIN is 2
            "grain_density": 4,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Chalk width below minimum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for chalk_width below minimum"
    except ValueError as e:
        print(f"✓ Caught expected error for chalk_width below minimum: {e}")

    # Above maximum
    try:
        stroke = {
            "type": "chalk",
            "points": [[100, 100], [200, 200]],
            "chalk_width": 100,  # MAX is 60
            "grain_density": 4,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Chalk width above maximum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for chalk_width above maximum"
    except ValueError as e:
        print(f"✓ Caught expected error for chalk_width above maximum: {e}")


def test_grain_density_out_of_range() -> None:
    """Test that validation raises ValueError for grain_density out of range."""
    print("\n=== Test: Grain Density Out of Range ===")
    renderer = ChalkRenderer()
    canvas_size = (800, 600)

    # Below minimum
    try:
        stroke: Stroke = {
            "type": "chalk",
            "points": [[100, 100], [200, 200]],
            "chalk_width": 20,
            "grain_density": 0,  # MIN is 1
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Grain density below minimum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for grain_density below minimum"
    except ValueError as e:
        print(f"✓ Caught expected error for grain_density below minimum: {e}")

    # Above maximum
    try:
        stroke = {
            "type": "chalk",
            "points": [[100, 100], [200, 200]],
            "chalk_width": 20,
            "grain_density": 10,  # MAX is 8
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Grain density above maximum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for grain_density above maximum"
    except ValueError as e:
        print(f"✓ Caught expected error for grain_density above maximum: {e}")


def test_points_validation() -> None:
    """Test points validation (too few, too many, out of bounds)."""
    print("\n=== Test: Points Validation ===")
    renderer = ChalkRenderer()
    canvas_size = (800, 600)

    # Too few points
    try:
        stroke: Stroke = {
            "type": "chalk",
            "points": [[100, 100]],  # Need at least 2
            "chalk_width": 20,
            "grain_density": 4,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Too few points",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for too few points"
    except ValueError as e:
        print(f"✓ Caught expected error for too few points: {e}")

    # Too many points
    try:
        points = [[i * 10, i * 10] for i in range(51)]  # MAX is 50
        stroke = {
            "type": "chalk",
            "points": points,
            "chalk_width": 20,
            "grain_density": 4,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Too many points",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for too many points"
    except ValueError as e:
        print(f"✓ Caught expected error for too many points: {e}")

    # Out of bounds point
    try:
        stroke = {
            "type": "chalk",
            "points": [[100, 100], [1000, 200]],  # x=1000 > canvas_width=800
            "chalk_width": 20,
            "grain_density": 4,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Out of bounds point",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for out of bounds point"
    except ValueError as e:
        print(f"✓ Caught expected error for out of bounds point: {e}")


def test_invalid_field_types() -> None:
    """Test that validation raises ValueError for invalid field types."""
    print("\n=== Test: Invalid Field Types ===")
    renderer = ChalkRenderer()
    canvas_size = (800, 600)

    # Non-integer chalk_width
    try:
        stroke: Stroke = {
            "type": "chalk",
            "points": [[100, 100], [200, 200]],
            "chalk_width": 20.5,  # type: ignore
            "grain_density": 4,
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Non-integer chalk_width",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for non-integer chalk_width"
    except ValueError as e:
        print(f"✓ Caught expected error for non-integer chalk_width: {e}")

    # Non-integer grain_density
    try:
        stroke = {
            "type": "chalk",
            "points": [[100, 100], [200, 200]],
            "chalk_width": 20,
            "grain_density": 4.5,  # type: ignore
            "color_hex": "#FFFFFF",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Non-integer grain_density",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for non-integer grain_density"
    except ValueError as e:
        print(f"✓ Caught expected error for non-integer grain_density: {e}")


def test_render_basic_chalk() -> None:
    """Test that basic chalk stroke renders without error."""
    print("\n=== Test: Basic Chalk Rendering ===")
    renderer = ChalkRenderer()

    canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    stroke: Stroke = {
        "type": "chalk",
        "points": [[100, 100], [200, 200], [300, 150]],
        "chalk_width": 20,
        "grain_density": 4,
        "color_hex": "#FF5733",
        "thickness": 5,
        "opacity": 0.7,
        "reasoning": "Basic chalk rendering test",
    }

    # Validate and render
    renderer.validate(stroke, canvas.size)
    renderer.render(stroke, draw)

    print("✓ Chalk stroke rendered successfully")

    # Save test image
    output_dir = project_root / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "chalk_test_basic.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


def test_render_varies_with_grain_density() -> None:
    """Test that grain_density affects pixel density."""
    print("\n=== Test: Grain Density Variation ===")

    def count_non_white_pixels(canvas: Image.Image) -> int:
        """Count pixels that are not white."""
        pixels = canvas.load()
        count = 0
        for y in range(canvas.height):
            for x in range(canvas.width):
                if pixels[x, y] != (255, 255, 255, 255):
                    count += 1
        return count

    renderer = ChalkRenderer()

    # Render with low grain_density
    canvas_low = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    draw_low = ImageDraw.Draw(canvas_low)

    stroke_low: Stroke = {
        "type": "chalk",
        "points": [[100, 100], [200, 200], [300, 150]],
        "chalk_width": 20,
        "grain_density": 1,
        "color_hex": "#000000",
        "thickness": 5,
        "opacity": 1.0,
        "reasoning": "Low grain density",
    }

    renderer.render(stroke_low, draw_low)
    low_pixel_count = count_non_white_pixels(canvas_low)

    # Render with high grain_density
    canvas_high = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    draw_high = ImageDraw.Draw(canvas_high)

    stroke_high: Stroke = {
        "type": "chalk",
        "points": [[100, 100], [200, 200], [300, 150]],
        "chalk_width": 20,
        "grain_density": 8,
        "color_hex": "#000000",
        "thickness": 5,
        "opacity": 1.0,
        "reasoning": "High grain density",
    }

    renderer.render(stroke_high, draw_high)
    high_pixel_count = count_non_white_pixels(canvas_high)

    print(f"  Low grain_density=1: {low_pixel_count} colored pixels")
    print(f"  High grain_density=8: {high_pixel_count} colored pixels")

    # High grain density should have significantly more colored pixels (at least 2x)
    assert high_pixel_count > low_pixel_count * 2, (
        f"High grain density should produce more pixels: {high_pixel_count} vs {low_pixel_count}"
    )

    # Save comparison image showing both grain densities
    canvas_comparison = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    draw_comparison = ImageDraw.Draw(canvas_comparison)

    # Draw low density on the left
    stroke_low_comparison: Stroke = {
        "type": "chalk",
        "points": [[100, 300], [200, 350], [300, 300]],
        "chalk_width": 20,
        "grain_density": 1,
        "color_hex": "#FF0000",
        "thickness": 5,
        "opacity": 0.8,
        "reasoning": "Low grain density comparison",
    }
    renderer.render(stroke_low_comparison, draw_comparison)

    # Draw high density on the right
    stroke_high_comparison: Stroke = {
        "type": "chalk",
        "points": [[500, 300], [600, 350], [700, 300]],
        "chalk_width": 20,
        "grain_density": 8,
        "color_hex": "#0000FF",
        "thickness": 5,
        "opacity": 0.8,
        "reasoning": "High grain density comparison",
    }
    renderer.render(stroke_high_comparison, draw_comparison)

    output_dir = project_root / "test_output"
    output_path = output_dir / "chalk_test_grain_density.png"
    canvas_comparison.save(output_path)
    print(f"✓ Comparison image saved to {output_path}")
    print(
        "✓ Visual confirmation: Left stroke (red) should be sparse, right (blue) should be dense"
    )

    print("✓ Grain density affects pixel density as expected")


def test_render_deterministic() -> None:
    """Test that same stroke rendered twice produces identical output."""
    print("\n=== Test: Deterministic Rendering ===")

    renderer = ChalkRenderer()

    # First render
    canvas1 = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    draw1 = ImageDraw.Draw(canvas1)

    stroke: Stroke = {
        "type": "chalk",
        "points": [[100, 100], [200, 200], [300, 150]],
        "chalk_width": 20,
        "grain_density": 4,
        "color_hex": "#FF5733",
        "thickness": 5,
        "opacity": 0.7,
        "reasoning": "Deterministic test",
    }

    renderer.render(stroke, draw1)

    # Second render
    canvas2 = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    draw2 = ImageDraw.Draw(canvas2)
    renderer.render(stroke, draw2)

    # Compare pixel by pixel
    pixels1 = canvas1.load()
    pixels2 = canvas2.load()

    for y in range(canvas1.height):
        for x in range(canvas1.width):
            assert pixels1[x, y] == pixels2[x, y], (
                f"Pixels differ at ({x}, {y}): {pixels1[x, y]} vs {pixels2[x, y]}"
            )

    print("✓ Deterministic rendering produces identical output")


if __name__ == "__main__":
    test_factory_registration()
    test_valid_chalk_stroke()
    test_missing_required_fields()
    test_chalk_width_out_of_range()
    test_grain_density_out_of_range()
    test_points_validation()
    test_invalid_field_types()
    test_render_basic_chalk()
    test_render_varies_with_grain_density()
    test_render_deterministic()

    print("\n" + "=" * 60)
    print("All ChalkRenderer tests passed! ✓")
    print("=" * 60)
