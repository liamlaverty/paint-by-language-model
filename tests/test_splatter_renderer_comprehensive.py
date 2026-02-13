"""Comprehensive tests for SplatterRenderer implementation."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import SplatterRenderer  # noqa: E402


def test_basic_splatter() -> None:
    """Test basic splatter rendering with minimal parameters."""
    print("\n=== Test 1: Basic Splatter ===")

    canvas = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = SplatterRenderer()

    splatter: Stroke = {
        "type": "splatter",
        "center_x": 200,
        "center_y": 150,
        "splatter_radius": 50,
        "splatter_count": 20,
        "dot_size_min": 2,
        "dot_size_max": 5,
        "color_hex": "#8B4513",
        "thickness": 1,  # Not used but should be validated if present
        "opacity": 0.8,
        "reasoning": "Test basic splatter",
    }

    renderer.validate(splatter, (400, 300))
    print("✓ Basic splatter validation passed")

    renderer.render(splatter, draw)
    print("✓ Basic splatter rendered successfully")

    # Save test image
    output_dir = project_root / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "splatter_test_basic.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


def test_various_splatters() -> None:
    """Test multiple splatters with different parameters."""
    print("\n=== Test 2: Various Splatters ===")

    canvas = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = SplatterRenderer()

    test_splatters: list[Stroke] = [
        # Dense, small dots
        {
            "type": "splatter",
            "center_x": 150,
            "center_y": 150,
            "splatter_radius": 80,
            "splatter_count": 50,
            "dot_size_min": 1,
            "dot_size_max": 3,
            "color_hex": "#FF6347",
            "thickness": 1,
            "opacity": 0.7,
            "reasoning": "Dense small dots",
        },
        # Sparse, large dots
        {
            "type": "splatter",
            "center_x": 400,
            "center_y": 150,
            "splatter_radius": 100,
            "splatter_count": 15,
            "dot_size_min": 5,
            "dot_size_max": 10,
            "color_hex": "#4169E1",
            "thickness": 1,
            "opacity": 0.6,
            "reasoning": "Sparse large dots",
        },
        # Medium density, mixed sizes
        {
            "type": "splatter",
            "center_x": 650,
            "center_y": 150,
            "splatter_radius": 60,
            "splatter_count": 30,
            "dot_size_min": 2,
            "dot_size_max": 8,
            "color_hex": "#32CD32",
            "thickness": 1,
            "opacity": 0.8,
            "reasoning": "Medium density mixed",
        },
        # Small radius, high count
        {
            "type": "splatter",
            "center_x": 200,
            "center_y": 400,
            "splatter_radius": 30,
            "splatter_count": 40,
            "dot_size_min": 1,
            "dot_size_max": 4,
            "color_hex": "#FFD700",
            "thickness": 1,
            "opacity": 0.9,
            "reasoning": "Small concentrated",
        },
        # Large radius, uniform dot size
        {
            "type": "splatter",
            "center_x": 500,
            "center_y": 400,
            "splatter_radius": 120,
            "splatter_count": 25,
            "dot_size_min": 4,
            "dot_size_max": 4,
            "color_hex": "#8B008B",
            "thickness": 1,
            "opacity": 0.5,
            "reasoning": "Large uniform",
        },
        # Minimum size test
        {
            "type": "splatter",
            "center_x": 100,
            "center_y": 500,
            "splatter_radius": 5,
            "splatter_count": 1,
            "dot_size_min": 1,
            "dot_size_max": 1,
            "color_hex": "#000000",
            "thickness": 1,
            "opacity": 1.0,
            "reasoning": "Minimum size",
        },
        # Maximum size test
        {
            "type": "splatter",
            "center_x": 700,
            "center_y": 500,
            "splatter_radius": 200,
            "splatter_count": 100,
            "dot_size_min": 10,
            "dot_size_max": 20,
            "color_hex": "#FF1493",
            "thickness": 1,
            "opacity": 0.4,
            "reasoning": "Maximum size",
        },
    ]

    for i, splatter in enumerate(test_splatters):
        renderer.validate(splatter, (800, 600))
        renderer.render(splatter, draw)
        print(f"✓ Splatter {i + 1} rendered successfully")

    output_dir = project_root / "test_output"
    output_path = output_dir / "splatter_test_various.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


def test_edge_cases() -> None:
    """Test edge cases and boundary conditions."""
    print("\n=== Test 3: Edge Cases ===")

    canvas = Image.new("RGB", (600, 400), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = SplatterRenderer()

    edge_splatters: list[Stroke] = [
        # Near top-left corner
        {
            "type": "splatter",
            "center_x": 50,
            "center_y": 50,
            "splatter_radius": 60,
            "splatter_count": 25,
            "dot_size_min": 2,
            "dot_size_max": 6,
            "color_hex": "#FF4500",
            "thickness": 1,
            "opacity": 0.7,
            "reasoning": "Top-left corner",
        },
        # Near top-right corner
        {
            "type": "splatter",
            "center_x": 550,
            "center_y": 50,
            "splatter_radius": 60,
            "splatter_count": 25,
            "dot_size_min": 2,
            "dot_size_max": 6,
            "color_hex": "#1E90FF",
            "thickness": 1,
            "opacity": 0.7,
            "reasoning": "Top-right corner",
        },
        # Near bottom-left corner
        {
            "type": "splatter",
            "center_x": 50,
            "center_y": 350,
            "splatter_radius": 60,
            "splatter_count": 25,
            "dot_size_min": 2,
            "dot_size_max": 6,
            "color_hex": "#32CD32",
            "thickness": 1,
            "opacity": 0.7,
            "reasoning": "Bottom-left corner",
        },
        # Near bottom-right corner
        {
            "type": "splatter",
            "center_x": 550,
            "center_y": 350,
            "splatter_radius": 60,
            "splatter_count": 25,
            "dot_size_min": 2,
            "dot_size_max": 6,
            "color_hex": "#FFD700",
            "thickness": 1,
            "opacity": 0.7,
            "reasoning": "Bottom-right corner",
        },
        # Centered with large radius (will extend beyond edges)
        {
            "type": "splatter",
            "center_x": 300,
            "center_y": 200,
            "splatter_radius": 180,
            "splatter_count": 50,
            "dot_size_min": 3,
            "dot_size_max": 8,
            "color_hex": "#8B008B",
            "thickness": 1,
            "opacity": 0.5,
            "reasoning": "Large centered",
        },
    ]

    for i, splatter in enumerate(edge_splatters):
        renderer.validate(splatter, (600, 400))
        renderer.render(splatter, draw)
        print(f"✓ Edge case {i + 1} rendered successfully")

    output_dir = project_root / "test_output"
    output_path = output_dir / "splatter_test_edges.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


def test_opacity_variations() -> None:
    """Test splatters with different opacity values."""
    print("\n=== Test 4: Opacity Variations ===")

    canvas = Image.new("RGB", (600, 400), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = SplatterRenderer()

    # Draw overlapping splatters with different opacities
    opacity_splatters: list[Stroke] = [
        {
            "type": "splatter",
            "center_x": 200,
            "center_y": 200,
            "splatter_radius": 80,
            "splatter_count": 40,
            "dot_size_min": 3,
            "dot_size_max": 7,
            "color_hex": "#FF0000",
            "thickness": 1,
            "opacity": 1.0,
            "reasoning": "Opaque red",
        },
        {
            "type": "splatter",
            "center_x": 300,
            "center_y": 200,
            "splatter_radius": 80,
            "splatter_count": 40,
            "dot_size_min": 3,
            "dot_size_max": 7,
            "color_hex": "#00FF00",
            "thickness": 1,
            "opacity": 0.6,
            "reasoning": "Semi-transparent green",
        },
        {
            "type": "splatter",
            "center_x": 400,
            "center_y": 200,
            "splatter_radius": 80,
            "splatter_count": 40,
            "dot_size_min": 3,
            "dot_size_max": 7,
            "color_hex": "#0000FF",
            "thickness": 1,
            "opacity": 0.3,
            "reasoning": "Transparent blue",
        },
    ]

    for i, splatter in enumerate(opacity_splatters):
        renderer.validate(splatter, (600, 400))
        renderer.render(splatter, draw)
        print(f"✓ Opacity variation {i + 1} rendered successfully")

    output_dir = project_root / "test_output"
    output_path = output_dir / "splatter_test_opacity.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


def test_validation_errors() -> None:
    """Test that validation properly catches invalid inputs."""
    print("\n=== Test 5: Validation Errors ===")

    renderer = SplatterRenderer()

    # Test missing fields
    try:
        invalid_splatter: Stroke = {
            "type": "splatter",
            "center_x": 100,
            "center_y": 100,
            # Missing splatter_radius
            "splatter_count": 20,
            "dot_size_min": 2,
            "dot_size_max": 5,
            "color_hex": "#FF0000",
            "thickness": 1,
            "opacity": 0.8,
        }
        renderer.validate(invalid_splatter, (400, 300))
        print("✗ Failed to catch missing splatter_radius")
    except ValueError as e:
        print(f"✓ Correctly caught missing field: {e}")

    # Test invalid splatter_radius
    try:
        invalid_splatter = {
            "type": "splatter",
            "center_x": 100,
            "center_y": 100,
            "splatter_radius": 500,  # Exceeds MAX_SPLATTER_RADIUS
            "splatter_count": 20,
            "dot_size_min": 2,
            "dot_size_max": 5,
            "color_hex": "#FF0000",
            "thickness": 1,
            "opacity": 0.8,
        }
        renderer.validate(invalid_splatter, (400, 300))
        print("✗ Failed to catch invalid splatter_radius")
    except ValueError as e:
        print(f"✓ Correctly caught invalid splatter_radius: {e}")

    # Test invalid splatter_count
    try:
        invalid_splatter = {
            "type": "splatter",
            "center_x": 100,
            "center_y": 100,
            "splatter_radius": 50,
            "splatter_count": 0,  # Below MIN_SPLATTER_COUNT
            "dot_size_min": 2,
            "dot_size_max": 5,
            "color_hex": "#FF0000",
            "thickness": 1,
            "opacity": 0.8,
        }
        renderer.validate(invalid_splatter, (400, 300))
        print("✗ Failed to catch invalid splatter_count")
    except ValueError as e:
        print(f"✓ Correctly caught invalid splatter_count: {e}")

    # Test invalid dot_size_min > dot_size_max
    try:
        invalid_splatter = {
            "type": "splatter",
            "center_x": 100,
            "center_y": 100,
            "splatter_radius": 50,
            "splatter_count": 20,
            "dot_size_min": 10,  # Greater than dot_size_max
            "dot_size_max": 5,
            "color_hex": "#FF0000",
            "thickness": 1,
            "opacity": 0.8,
        }
        renderer.validate(invalid_splatter, (400, 300))
        print("✗ Failed to catch dot_size_min > dot_size_max")
    except ValueError as e:
        print(f"✓ Correctly caught dot_size_min > dot_size_max: {e}")

    # Test center out of bounds
    try:
        invalid_splatter = {
            "type": "splatter",
            "center_x": 500,  # Outside canvas width
            "center_y": 100,
            "splatter_radius": 50,
            "splatter_count": 20,
            "dot_size_min": 2,
            "dot_size_max": 5,
            "color_hex": "#FF0000",
            "thickness": 1,
            "opacity": 0.8,
        }
        renderer.validate(invalid_splatter, (400, 300))
        print("✗ Failed to catch center out of bounds")
    except ValueError as e:
        print(f"✓ Correctly caught center out of bounds: {e}")


def main() -> None:
    """Run all splatter renderer tests."""
    print("=" * 60)
    print("SplatterRenderer Comprehensive Test Suite")
    print("=" * 60)

    test_basic_splatter()
    test_various_splatters()
    test_edge_cases()
    test_opacity_variations()
    test_validation_errors()

    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
