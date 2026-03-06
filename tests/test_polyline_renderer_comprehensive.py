"""Test PolylineRenderer with visual output of various polyline scenarios."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import PolylineRenderer, StrokeRendererFactory  # noqa: E402


def test_factory_registration() -> None:
    """Test that PolylineRenderer is registered in factory."""
    renderer = StrokeRendererFactory.get_renderer("polyline")
    assert isinstance(renderer, PolylineRenderer)
    print("✓ Factory returns PolylineRenderer for 'polyline' type")


def test_various_polylines() -> None:
    """Test rendering various polyline configurations."""
    canvas = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = PolylineRenderer()

    # Test cases: simple zigzag, smooth curve, sharp angles, two-point line, dense points
    test_cases: list[Stroke] = [
        {
            "type": "polyline",
            "points": [[50, 50], [100, 150], [150, 50], [200, 150], [250, 50]],
            "color_hex": "#FF0000",
            "thickness": 3,
            "opacity": 1.0,
            "reasoning": "Simple zigzag pattern",
        },
        {
            "type": "polyline",
            "points": [
                [300, 50],
                [330, 80],
                [360, 100],
                [390, 110],
                [420, 100],
                [450, 80],
                [480, 50],
            ],
            "color_hex": "#00AA00",
            "thickness": 4,
            "opacity": 0.8,
            "reasoning": "Smooth curve (arc simulation)",
        },
        {
            "type": "polyline",
            "points": [[550, 50], [600, 50], [600, 150], [550, 150], [550, 100]],
            "color_hex": "#0000FF",
            "thickness": 2,
            "opacity": 0.9,
            "reasoning": "Sharp angles (rectangular path)",
        },
        {
            "type": "polyline",
            "points": [[700, 50], [750, 150]],
            "color_hex": "#FF00FF",
            "thickness": 5,
            "opacity": 1.0,
            "reasoning": "Two-point polyline (simple line)",
        },
        {
            "type": "polyline",
            "points": [
                [50, 250],
                [80, 280],
                [110, 250],
                [140, 270],
                [170, 240],
                [200, 260],
                [230, 230],
                [260, 250],
                [290, 220],
                [320, 240],
            ],
            "color_hex": "#FF8800",
            "thickness": 2,
            "opacity": 0.7,
            "reasoning": "Organic wavy line (many points)",
        },
        {
            "type": "polyline",
            "points": [
                [400, 250],
                [450, 250],
                [450, 300],
                [500, 300],
                [500, 250],
                [550, 250],
                [550, 300],
                [600, 300],
            ],
            "color_hex": "#8800FF",
            "thickness": 3,
            "opacity": 0.85,
            "reasoning": "Step pattern",
        },
        {
            "type": "polyline",
            "points": [
                [50, 400],
                [100, 350],
                [150, 450],
                [200, 380],
                [250, 470],
                [300, 400],
                [350, 450],
                [400, 390],
            ],
            "color_hex": "#00CCCC",
            "thickness": 4,
            "opacity": 0.6,
            "reasoning": "Gestural brushstroke (expressive line)",
        },
        {
            "type": "polyline",
            "points": [
                [450, 400],
                [455, 405],
                [460, 408],
                [465, 410],
                [470, 411],
                [475, 410],
                [480, 408],
                [485, 405],
                [490, 400],
                [495, 395],
                [500, 392],
                [505, 390],
                [510, 392],
                [515, 395],
                [520, 400],
            ],
            "color_hex": "#CC0088",
            "thickness": 2,
            "opacity": 0.9,
            "reasoning": "Dense smooth curve (15 points)",
        },
        {
            "type": "polyline",
            "points": [[600, 450], [650, 400], [700, 450], [750, 400]],
            "color_hex": "#888800",
            "thickness": 6,
            "opacity": 0.75,
            "reasoning": "Thick zigzag (bold stroke)",
        },
        {
            "type": "polyline",
            "points": [
                [50, 550],
                [150, 520],
                [250, 540],
                [350, 510],
                [450, 530],
                [550, 500],
                [650, 520],
                [750, 490],
            ],
            "color_hex": "#008888",
            "thickness": 1,
            "opacity": 0.5,
            "reasoning": "Thin flowing line (minimal opacity)",
        },
    ]

    for i, stroke in enumerate(test_cases):
        renderer.validate(stroke, (800, 600))
        renderer.render(stroke, draw)
        print(f"✓ Test case {i + 1}: {stroke['reasoning']}")

    # Save test image
    output_dir = project_root / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "polyline_test_various.png"
    canvas.save(output_path)
    print(f"✓ All polyline variations saved to {output_path}")


def test_validation_errors() -> None:
    """Test that validation catches invalid polyline strokes."""
    renderer = PolylineRenderer()
    canvas_size = (400, 300)

    # Test 1: Missing required field
    try:
        stroke: Stroke = {
            "type": "polyline",
            "color_hex": "#228B22",
            "thickness": 2,
            "opacity": 0.7,
            "reasoning": "Missing points",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing points"
    except ValueError as e:
        print(f"✓ Caught expected error for missing field: {e}")

    # Test 2: Too few points (1 point)
    try:
        stroke = {
            "type": "polyline",
            "points": [[50, 50]],
            "color_hex": "#228B22",
            "thickness": 2,
            "opacity": 0.7,
            "reasoning": "Only one point",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for too few points"
    except ValueError as e:
        print(f"✓ Caught expected error for too few points: {e}")

    # Test 3: Too many points (>50)
    try:
        points = [[i * 5, i * 3] for i in range(51)]
        stroke = {
            "type": "polyline",
            "points": points,
            "color_hex": "#228B22",
            "thickness": 2,
            "opacity": 0.7,
            "reasoning": "51 points",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for too many points"
    except ValueError as e:
        print(f"✓ Caught expected error for too many points: {e}")

    # Test 4: Out of bounds coordinates
    try:
        stroke = {
            "type": "polyline",
            "points": [[50, 50], [500, 100]],  # x=500 > 400
            "color_hex": "#228B22",
            "thickness": 2,
            "opacity": 0.7,
            "reasoning": "Out of bounds",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for out of bounds"
    except ValueError as e:
        print(f"✓ Caught expected error for out of bounds: {e}")


if __name__ == "__main__":
    test_factory_registration()
    test_various_polylines()
    test_validation_errors()
    print("\n✓ All PolylineRenderer comprehensive tests passed!")
