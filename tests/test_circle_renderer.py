"""Simple test to verify CircleRenderer implementation."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import CircleRenderer  # noqa: E402


def test_circle_renderer() -> None:
    """Test basic circle rendering."""
    # Create a simple canvas
    canvas = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(canvas)

    # Create a circle renderer
    renderer = CircleRenderer()

    # Test filled circle stroke
    filled_circle: Stroke = {
        "type": "circle",
        "center_x": 100,
        "center_y": 100,
        "radius": 50,
        "fill": True,
        "color_hex": "#FFD700",
        "thickness": 2,
        "opacity": 0.8,
        "reasoning": "Test filled circle",
    }

    # Validate the stroke
    renderer.validate(filled_circle, (400, 300))
    print("✓ Filled circle stroke validation passed")

    # Render the stroke
    renderer.render(filled_circle, draw)
    print("✓ Filled circle stroke rendered successfully")

    # Test outline circle stroke
    outline_circle: Stroke = {
        "type": "circle",
        "center_x": 250,
        "center_y": 150,
        "radius": 70,
        "fill": False,
        "color_hex": "#0066CC",
        "thickness": 5,
        "opacity": 1.0,
        "reasoning": "Test outline circle",
    }

    # Validate and render outline circle
    renderer.validate(outline_circle, (400, 300))
    print("✓ Outline circle stroke validation passed")

    renderer.render(outline_circle, draw)
    print("✓ Outline circle stroke rendered successfully")

    # Save test image
    output_dir = project_root / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "circle_test.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


if __name__ == "__main__":
    test_circle_renderer()
    print("\nAll tests passed! ✓")
