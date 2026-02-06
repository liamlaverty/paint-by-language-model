"""Test CircleRenderer factory registration and various circle scenarios."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import CircleRenderer, StrokeRendererFactory  # noqa: E402


def test_factory_registration() -> None:
    """Test that CircleRenderer is registered in factory."""
    renderer = StrokeRendererFactory.get_renderer("circle")
    assert isinstance(renderer, CircleRenderer)
    print("✓ Factory returns CircleRenderer for 'circle' type")


def test_various_circles() -> None:
    """Test rendering various circle configurations."""
    canvas = Image.new("RGB", (700, 500), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = CircleRenderer()

    # Test cases: filled circles, outline circles, different sizes and opacities
    test_cases: list[Stroke] = [
        {
            "type": "circle",
            "center_x": 100,
            "center_y": 100,
            "radius": 50,
            "fill": True,
            "color_hex": "#FFD700",
            "thickness": 2,
            "opacity": 1.0,
            "reasoning": "Solid filled circle (gold)",
        },
        {
            "type": "circle",
            "center_x": 250,
            "center_y": 100,
            "radius": 60,
            "fill": False,
            "color_hex": "#FF0000",
            "thickness": 3,
            "opacity": 1.0,
            "reasoning": "Outline circle (red)",
        },
        {
            "type": "circle",
            "center_x": 420,
            "center_y": 100,
            "radius": 70,
            "fill": True,
            "color_hex": "#0066CC",
            "thickness": 2,
            "opacity": 0.5,
            "reasoning": "Semi-transparent filled circle (blue)",
        },
        {
            "type": "circle",
            "center_x": 600,
            "center_y": 100,
            "radius": 80,
            "fill": False,
            "color_hex": "#00CC66",
            "thickness": 8,
            "opacity": 0.7,
            "reasoning": "Thick outline with transparency (green)",
        },
        {
            "type": "circle",
            "center_x": 100,
            "center_y": 280,
            "radius": 5,
            "fill": True,
            "color_hex": "#000000",
            "thickness": 1,
            "opacity": 1.0,
            "reasoning": "Tiny dot (min radius)",
        },
        {
            "type": "circle",
            "center_x": 180,
            "center_y": 280,
            "radius": 15,
            "fill": True,
            "color_hex": "#FF6600",
            "thickness": 1,
            "opacity": 0.8,
            "reasoning": "Small filled circle (orange)",
        },
        {
            "type": "circle",
            "center_x": 280,
            "center_y": 280,
            "radius": 25,
            "fill": False,
            "color_hex": "#CC00FF",
            "thickness": 2,
            "opacity": 0.9,
            "reasoning": "Medium outline (purple)",
        },
        {
            "type": "circle",
            "center_x": 420,
            "center_y": 300,
            "radius": 90,
            "fill": True,
            "color_hex": "#FFCC00",
            "thickness": 1,
            "opacity": 0.3,
            "reasoning": "Large transparent filled circle (yellow)",
        },
        {
            "type": "circle",
            "center_x": 580,
            "center_y": 300,
            "radius": 90,
            "fill": False,
            "color_hex": "#006699",
            "thickness": 5,
            "opacity": 0.6,
            "reasoning": "Very large outline (teal)",
        },
    ]

    for i, stroke in enumerate(test_cases):
        renderer.validate(stroke, (700, 500))
        renderer.render(stroke, draw)
        print(f"✓ Test case {i + 1}: {stroke['reasoning']}")

    # Save test image
    output_dir = project_root / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "circle_test_various.png"
    canvas.save(output_path)
    print(f"✓ All circle variations saved to {output_path}")


def test_edge_cases() -> None:
    """Test edge cases for circle rendering."""
    canvas = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = CircleRenderer()

    # Test edge-touching circles
    edge_cases: list[Stroke] = [
        {
            "type": "circle",
            "center_x": 50,
            "center_y": 50,
            "radius": 50,
            "fill": False,
            "color_hex": "#FF0000",
            "thickness": 2,
            "opacity": 1.0,
            "reasoning": "Top-left corner touch",
        },
        {
            "type": "circle",
            "center_x": 349,
            "center_y": 50,
            "radius": 50,
            "fill": False,
            "color_hex": "#00FF00",
            "thickness": 2,
            "opacity": 1.0,
            "reasoning": "Top-right corner touch",
        },
        {
            "type": "circle",
            "center_x": 50,
            "center_y": 249,
            "radius": 50,
            "fill": False,
            "color_hex": "#0000FF",
            "thickness": 2,
            "opacity": 1.0,
            "reasoning": "Bottom-left corner touch",
        },
        {
            "type": "circle",
            "center_x": 349,
            "center_y": 249,
            "radius": 50,
            "fill": False,
            "color_hex": "#FFFF00",
            "thickness": 2,
            "opacity": 1.0,
            "reasoning": "Bottom-right corner touch",
        },
    ]

    for i, stroke in enumerate(edge_cases):
        renderer.validate(stroke, (400, 300))
        renderer.render(stroke, draw)
        print(f"✓ Edge case {i + 1}: {stroke['reasoning']}")

    # Save test image
    output_dir = project_root / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "circle_test_edges.png"
    canvas.save(output_path)
    print(f"✓ Edge case circles saved to {output_path}")


def test_validation_errors() -> None:
    """Test that validation catches invalid circle strokes."""
    renderer = CircleRenderer()
    canvas_size = (400, 300)

    # Test 1: Missing required field
    try:
        stroke: Stroke = {
            "type": "circle",
            "center_y": 150,
            "radius": 50,
            "fill": True,
            "color_hex": "#FFD700",
            "thickness": 2,
            "opacity": 0.8,
            "reasoning": "Missing center_x",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing center_x"
    except ValueError as e:
        print(f"✓ Caught expected error for missing field: {e}")

    # Test 2: Radius too large
    try:
        stroke = {
            "type": "circle",
            "center_x": 200,
            "center_y": 150,
            "radius": 500,  # > MAX_CIRCLE_RADIUS (400)
            "fill": True,
            "color_hex": "#FFD700",
            "thickness": 2,
            "opacity": 0.8,
            "reasoning": "Radius too large",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for radius too large"
    except ValueError as e:
        print(f"✓ Caught expected error for large radius: {e}")

    # Test 3: Circle extends beyond canvas (left edge)
    try:
        stroke = {
            "type": "circle",
            "center_x": 30,
            "center_y": 150,
            "radius": 50,  # Would go to x=-20
            "fill": True,
            "color_hex": "#FFD700",
            "thickness": 2,
            "opacity": 0.8,
            "reasoning": "Extends beyond left edge",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for extending beyond left edge"
    except ValueError as e:
        print(f"✓ Caught expected error for left edge violation: {e}")

    # Test 4: Circle extends beyond canvas (right edge)
    try:
        stroke = {
            "type": "circle",
            "center_x": 380,
            "center_y": 150,
            "radius": 50,  # Would go to x=430
            "fill": True,
            "color_hex": "#FFD700",
            "thickness": 2,
            "opacity": 0.8,
            "reasoning": "Extends beyond right edge",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for extending beyond right edge"
    except ValueError as e:
        print(f"✓ Caught expected error for right edge violation: {e}")

    # Test 5: Invalid fill type
    try:
        stroke = {
            "type": "circle",
            "center_x": 200,
            "center_y": 150,
            "radius": 50,
            "fill": "yes",  # Should be boolean
            "color_hex": "#FFD700",
            "thickness": 2,
            "opacity": 0.8,
            "reasoning": "Invalid fill type",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for invalid fill type"
    except ValueError as e:
        print(f"✓ Caught expected error for invalid fill type: {e}")

    # Test 6: Negative radius
    try:
        stroke = {
            "type": "circle",
            "center_x": 200,
            "center_y": 150,
            "radius": -10,
            "fill": True,
            "color_hex": "#FFD700",
            "thickness": 2,
            "opacity": 0.8,
            "reasoning": "Negative radius",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for negative radius"
    except ValueError as e:
        print(f"✓ Caught expected error for negative radius: {e}")

    # Test 7: Invalid color format
    try:
        stroke = {
            "type": "circle",
            "center_x": 200,
            "center_y": 150,
            "radius": 50,
            "fill": True,
            "color_hex": "gold",  # Not hex format
            "thickness": 2,
            "opacity": 0.8,
            "reasoning": "Invalid color",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for invalid color"
    except ValueError as e:
        print(f"✓ Caught expected error for invalid color: {e}")


if __name__ == "__main__":
    print("=== Testing CircleRenderer ===\n")

    print("Test 1: Factory Registration")
    test_factory_registration()
    print()

    print("Test 2: Various Circle Configurations")
    test_various_circles()
    print()

    print("Test 3: Edge Cases")
    test_edge_cases()
    print()

    print("Test 4: Validation Errors")
    test_validation_errors()
    print()

    print("=" * 40)
    print("All tests passed! ✓")
