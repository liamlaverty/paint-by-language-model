"""Simple test to verify ArcRenderer implementation."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import ArcRenderer  # noqa: E402


def test_arc_renderer() -> None:
    """Test basic arc rendering."""
    # Create a simple canvas
    canvas = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(canvas)

    # Create an arc renderer
    renderer = ArcRenderer()

    # Test arc stroke
    arc_stroke: Stroke = {
        "type": "arc",
        "arc_bbox": [50, 50, 200, 150],
        "arc_start_angle": 0,
        "arc_end_angle": 180,
        "color_hex": "#0066CC",
        "thickness": 3,
        "opacity": 0.9,
        "reasoning": "Test arc",
    }

    # Validate the stroke
    renderer.validate(arc_stroke, (400, 300))
    print("✓ Arc stroke validation passed")

    # Render the stroke
    renderer.render(arc_stroke, draw)
    print("✓ Arc stroke rendered successfully")

    # Save test image
    output_path = "test_output/arc_test.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


if __name__ == "__main__":
    test_arc_renderer()
    print("\nAll tests passed! ✓")
