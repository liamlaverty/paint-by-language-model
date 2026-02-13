"""Simple test to verify SplatterRenderer implementation."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import SplatterRenderer  # noqa: E402


def test_splatter_renderer() -> None:
    """Test basic splatter rendering."""
    # Create a simple canvas
    canvas = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(canvas)

    # Create a splatter renderer
    renderer = SplatterRenderer()

    # Test basic splatter stroke
    splatter: Stroke = {
        "type": "splatter",
        "center_x": 200,
        "center_y": 150,
        "splatter_radius": 60,
        "splatter_count": 30,
        "dot_size_min": 2,
        "dot_size_max": 6,
        "color_hex": "#8B4513",
        "thickness": 1,
        "opacity": 0.7,
        "reasoning": "Test splatter",
    }

    # Validate the stroke
    renderer.validate(splatter, (400, 300))
    print("✓ Splatter stroke validation passed")

    # Render the stroke
    renderer.render(splatter, draw)
    print("✓ Splatter stroke rendered successfully")

    # Save test image
    output_dir = project_root / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "splatter_test.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


if __name__ == "__main__":
    test_splatter_renderer()
    print("\nAll tests passed! ✓")
