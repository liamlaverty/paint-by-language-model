"""Comprehensive tests for DryBrushRenderer implementation."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.renderers import DryBrushRenderer, StrokeRendererFactory  # noqa: E402


def test_factory_registration() -> None:
    """Test that DryBrushRenderer is registered in factory."""
    print("\n=== Test: Factory Registration ===")
    renderer = StrokeRendererFactory.get_renderer("dry-brush")
    assert isinstance(renderer, DryBrushRenderer)
    print("✓ Factory returns DryBrushRenderer for 'dry-brush' type")


def test_valid_dry_brush_stroke() -> None:
    """Test validation passes with all valid fields."""
    print("\n=== Test: Valid Dry-Brush Stroke ===")
    renderer = DryBrushRenderer()
    canvas_size = (800, 600)

    stroke: Stroke = {
        "type": "dry-brush",
        "points": [[100, 100], [200, 200], [300, 150]],
        "brush_width": 20,
        "bristle_count": 10,
        "gap_probability": 0.3,
        "color_hex": "#8B4513",
        "thickness": 5,
        "opacity": 0.8,
        "reasoning": "Valid dry-brush stroke",
    }

    renderer.validate(stroke, canvas_size)
    print("✓ Valid dry-brush stroke passed validation")


def test_missing_required_fields() -> None:
    """Test that validation raises ValueError for missing required fields."""
    print("\n=== Test: Missing Required Fields ===")
    renderer = DryBrushRenderer()
    canvas_size = (800, 600)

    # Missing points
    try:
        stroke: Stroke = {
            "type": "dry-brush",
            "brush_width": 20,
            "bristle_count": 10,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Missing points",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing points"
    except ValueError as e:
        print(f"✓ Caught expected error for missing points: {e}")

    # Missing brush_width
    try:
        stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "bristle_count": 10,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Missing brush_width",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing brush_width"
    except ValueError as e:
        print(f"✓ Caught expected error for missing brush_width: {e}")

    # Missing bristle_count
    try:
        stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 20,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Missing bristle_count",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing bristle_count"
    except ValueError as e:
        print(f"✓ Caught expected error for missing bristle_count: {e}")

    # Missing gap_probability
    try:
        stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 20,
            "bristle_count": 10,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Missing gap_probability",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for missing gap_probability"
    except ValueError as e:
        print(f"✓ Caught expected error for missing gap_probability: {e}")


def test_brush_width_out_of_range() -> None:
    """Test that validation raises ValueError for brush_width out of range."""
    print("\n=== Test: Brush Width Out of Range ===")
    renderer = DryBrushRenderer()
    canvas_size = (800, 600)

    # Below minimum
    try:
        stroke: Stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 2,  # MIN is 4
            "bristle_count": 10,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Brush width below minimum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for brush_width below minimum"
    except ValueError as e:
        print(f"✓ Caught expected error for brush_width below minimum: {e}")

    # Above maximum
    try:
        stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 150,  # MAX is 100
            "bristle_count": 10,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Brush width above maximum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for brush_width above maximum"
    except ValueError as e:
        print(f"✓ Caught expected error for brush_width above maximum: {e}")


def test_bristle_count_out_of_range() -> None:
    """Test that validation raises ValueError for bristle_count out of range."""
    print("\n=== Test: Bristle Count Out of Range ===")
    renderer = DryBrushRenderer()
    canvas_size = (800, 600)

    # Below minimum
    try:
        stroke: Stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 20,
            "bristle_count": 1,  # MIN is 3
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Bristle count below minimum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for bristle_count below minimum"
    except ValueError as e:
        print(f"✓ Caught expected error for bristle_count below minimum: {e}")

    # Above maximum
    try:
        stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 20,
            "bristle_count": 25,  # MAX is 20
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Bristle count above maximum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for bristle_count above maximum"
    except ValueError as e:
        print(f"✓ Caught expected error for bristle_count above maximum: {e}")


def test_gap_probability_out_of_range() -> None:
    """Test that validation raises ValueError for gap_probability out of range."""
    print("\n=== Test: Gap Probability Out of Range ===")
    renderer = DryBrushRenderer()
    canvas_size = (800, 600)

    # Below minimum
    try:
        stroke: Stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 20,
            "bristle_count": 10,
            "gap_probability": -0.1,  # MIN is 0.0
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Gap probability below minimum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for gap_probability below minimum"
    except ValueError as e:
        print(f"✓ Caught expected error for gap_probability below minimum: {e}")

    # Above maximum
    try:
        stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 20,
            "bristle_count": 10,
            "gap_probability": 0.9,  # MAX is 0.7
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Gap probability above maximum",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for gap_probability above maximum"
    except ValueError as e:
        print(f"✓ Caught expected error for gap_probability above maximum: {e}")


def test_points_validation() -> None:
    """Test that validation catches invalid points configurations."""
    print("\n=== Test: Points Validation ===")
    renderer = DryBrushRenderer()
    canvas_size = (800, 600)

    # Too few points
    try:
        stroke: Stroke = {
            "type": "dry-brush",
            "points": [[100, 100]],  # Only 1 point, need at least 2
            "brush_width": 20,
            "bristle_count": 10,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
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
        points = [[i * 10, i * 10] for i in range(51)]  # 51 points, max is 50
        stroke = {
            "type": "dry-brush",
            "points": points,
            "brush_width": 20,
            "bristle_count": 10,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Too many points",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for too many points"
    except ValueError as e:
        print(f"✓ Caught expected error for too many points: {e}")

    # Out-of-bounds points
    try:
        stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [900, 200]],  # x=900 > 800
            "brush_width": 20,
            "bristle_count": 10,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Out of bounds",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for out-of-bounds points"
    except ValueError as e:
        print(f"✓ Caught expected error for out-of-bounds points: {e}")


def test_invalid_field_types() -> None:
    """Test that validation catches invalid field types."""
    print("\n=== Test: Invalid Field Types ===")
    renderer = DryBrushRenderer()
    canvas_size = (800, 600)

    # Non-integer brush_width
    try:
        stroke: Stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 20.5,  # Should be int
            "bristle_count": 10,
            "gap_probability": 0.3,
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "Non-integer brush_width",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for non-integer brush_width"
    except ValueError as e:
        print(f"✓ Caught expected error for non-integer brush_width: {e}")

    # Non-number gap_probability (string)
    try:
        stroke = {
            "type": "dry-brush",
            "points": [[100, 100], [200, 200]],
            "brush_width": 20,
            "bristle_count": 10,
            "gap_probability": "0.3",  # Should be float
            "color_hex": "#8B4513",
            "thickness": 5,
            "opacity": 0.8,
            "reasoning": "String gap_probability",
        }
        renderer.validate(stroke, canvas_size)
        assert False, "Should have raised ValueError for string gap_probability"
    except ValueError as e:
        print(f"✓ Caught expected error for string gap_probability: {e}")


def test_render_basic_dry_brush() -> None:
    """Test basic dry-brush rendering without error."""
    print("\n=== Test: Render Basic Dry-Brush ===")
    canvas = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = DryBrushRenderer()

    stroke: Stroke = {
        "type": "dry-brush",
        "points": [[50, 50], [150, 100], [250, 80], [350, 120]],
        "brush_width": 15,
        "bristle_count": 8,
        "gap_probability": 0.4,
        "color_hex": "#8B4513",
        "thickness": 8,
        "opacity": 0.7,
        "reasoning": "Basic dry-brush test",
    }

    renderer.validate(stroke, (400, 300))
    renderer.render(stroke, draw)
    print("✓ Basic dry-brush rendered successfully")

    # Save test image
    output_dir = project_root / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "dry_brush_test_basic.png"
    canvas.save(output_path)
    print(f"✓ Test image saved to {output_path}")


def test_render_varies_with_gap_probability() -> None:
    """Test that gap_probability affects rendering output."""
    print("\n=== Test: Gap Probability Variations ===")
    canvas = Image.new("RGB", (800, 300), "white")
    draw = ImageDraw.Draw(canvas)
    renderer = DryBrushRenderer()

    # Stroke with gap_probability = 0.0 (no gaps)
    stroke_no_gaps: Stroke = {
        "type": "dry-brush",
        "points": [[50, 100], [150, 150], [250, 100]],
        "brush_width": 20,
        "bristle_count": 10,
        "gap_probability": 0.0,
        "color_hex": "#FF0000",
        "thickness": 10,
        "opacity": 0.8,
        "reasoning": "No gaps",
    }

    # Stroke with gap_probability = 0.7 (many gaps)
    stroke_many_gaps: Stroke = {
        "type": "dry-brush",
        "points": [[450, 100], [550, 150], [650, 100]],
        "brush_width": 20,
        "bristle_count": 10,
        "gap_probability": 0.7,
        "color_hex": "#0000FF",
        "thickness": 10,
        "opacity": 0.8,
        "reasoning": "Many gaps",
    }

    renderer.validate(stroke_no_gaps, (800, 300))
    renderer.render(stroke_no_gaps, draw)
    print("✓ Rendered stroke with gap_probability=0.0")

    renderer.validate(stroke_many_gaps, (800, 300))
    renderer.render(stroke_many_gaps, draw)
    print("✓ Rendered stroke with gap_probability=0.7")

    # Save comparison image
    output_dir = project_root / "test_output"
    output_path = output_dir / "dry_brush_test_gap_probability.png"
    canvas.save(output_path)
    print(f"✓ Comparison image saved to {output_path}")
    print("✓ Visual confirmation: Left stroke should be solid, right should have gaps")


if __name__ == "__main__":
    test_factory_registration()
    test_valid_dry_brush_stroke()
    test_missing_required_fields()
    test_brush_width_out_of_range()
    test_bristle_count_out_of_range()
    test_gap_probability_out_of_range()
    test_points_validation()
    test_invalid_field_types()
    test_render_basic_dry_brush()
    test_render_varies_with_gap_probability()
    print("\n✓ All DryBrushRenderer comprehensive tests passed!")
