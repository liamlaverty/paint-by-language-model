"""Test ArcRenderer factory registration and various arc scenarios."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import ArcRenderer, StrokeRendererFactory  # noqa: E402


def test_factory_registration() -> None:
    """Test that ArcRenderer is registered in factory."""
    renderer = StrokeRendererFactory.get_renderer("arc")
    assert isinstance(renderer, ArcRenderer)
    print("✓ Factory returns ArcRenderer for 'arc' type")


def test_various_arcs() -> None:
    """Test rendering various arc configurations."""
    canvas = Image.new("RGB", (600, 400), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = ArcRenderer()

    # Test cases: quarter circle, half circle, full circle, wraparound
    test_cases: list[Stroke] = [
        {
            "type": "arc",
            "arc_bbox": [50, 50, 150, 150],
            "arc_start_angle": 0,
            "arc_end_angle": 90,
            "color_hex": "#FF0000",
            "thickness": 3,
            "opacity": 1.0,
            "reasoning": "Quarter circle (0-90°)",
        },
        {
            "type": "arc",
            "arc_bbox": [200, 50, 350, 150],
            "arc_start_angle": 0,
            "arc_end_angle": 180,
            "color_hex": "#00FF00",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Half circle (0-180°)",
        },
        {
            "type": "arc",
            "arc_bbox": [400, 50, 550, 150],
            "arc_start_angle": 0,
            "arc_end_angle": 360,
            "color_hex": "#0000FF",
            "thickness": 2,
            "opacity": 0.6,
            "reasoning": "Full ellipse (0-360°)",
        },
        {
            "type": "arc",
            "arc_bbox": [50, 200, 200, 350],
            "arc_start_angle": 270,
            "arc_end_angle": 90,
            "color_hex": "#FF00FF",
            "thickness": 4,
            "opacity": 0.9,
            "reasoning": "Wraparound arc (270-90°)",
        },
        {
            "type": "arc",
            "arc_bbox": [250, 250, 350, 300],
            "arc_start_angle": 45,
            "arc_end_angle": 315,
            "color_hex": "#00FFFF",
            "thickness": 5,
            "opacity": 0.7,
            "reasoning": "Elliptical arc (45-315°)",
        },
    ]

    for i, stroke in enumerate(test_cases):
        renderer.validate(stroke, (600, 400))
        renderer.render(stroke, draw)
        print(f"✓ Test case {i + 1}: {stroke['reasoning']}")

    # Save test image
    output_path = "test_output/arc_test_various.png"
    canvas.save(output_path)
    print(f"✓ All arc variations saved to {output_path}")


def test_validation_errors() -> None:
    """Test that validation catches invalid arc strokes."""
    renderer = ArcRenderer()
    canvas_size = (400, 300)

    # Test 1: Missing required field
    try:
        stroke: Stroke = {
            "type": "arc",
            "arc_start_angle": 0,
            "arc_end_angle": 180,
            "color_hex": "#0066CC",
            "thickness": 3,
            "opacity": 0.9,
            "reasoning": "Missing arc_bbox",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing arc_bbox"
    except ValueError as e:
        print(f"✓ Caught expected error for missing field: {e}")

    # Test 2: Invalid bounding box (x0 >= x1)
    try:
        stroke = {
            "type": "arc",
            "arc_bbox": [200, 50, 100, 150],  # x0 > x1
            "arc_start_angle": 0,
            "arc_end_angle": 180,
            "color_hex": "#0066CC",
            "thickness": 3,
            "opacity": 0.9,
            "reasoning": "Invalid bbox",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for invalid bbox"
    except ValueError as e:
        print(f"✓ Caught expected error for invalid bbox: {e}")

    # Test 3: Out of bounds angle
    try:
        stroke = {
            "type": "arc",
            "arc_bbox": [50, 50, 200, 150],
            "arc_start_angle": 0,
            "arc_end_angle": 400,  # > 360
            "color_hex": "#0066CC",
            "thickness": 3,
            "opacity": 0.9,
            "reasoning": "Invalid angle",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for out of range angle"
    except ValueError as e:
        print(f"✓ Caught expected error for invalid angle: {e}")


if __name__ == "__main__":
    test_factory_registration()
    test_various_arcs()
    test_validation_errors()
    print("\n✓ All ArcRenderer tests passed!")
