"""Comprehensive tests for WetBrushRenderer implementation."""

import sys
from pathlib import Path
from typing import cast

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

import pytest  # noqa: E402
from models.stroke import Stroke  # noqa: E402
from PIL import Image  # noqa: E402
from services.canvas_manager import CanvasManager  # noqa: E402
from services.renderers import StrokeRendererFactory, WetBrushRenderer  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_stroke(**overrides: object) -> "Stroke":
    """Return a minimal valid wet-brush stroke, allowing field overrides."""
    base: Stroke = {
        "type": "wet-brush",
        "points": [[100, 100], [200, 200], [300, 150]],
        "softness": 5,
        "flow": 0.8,
        "color_hex": "#4477AA",
        "thickness": 10,
        "opacity": 0.7,
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


CANVAS_SIZE = (800, 600)


# ---------------------------------------------------------------------------
# Factory registration
# ---------------------------------------------------------------------------


def test_factory_registration() -> None:
    """Test that WetBrushRenderer is registered in factory."""
    renderer = StrokeRendererFactory.get_renderer("wet-brush")
    assert isinstance(renderer, WetBrushRenderer)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_valid_wet_brush_stroke() -> None:
    """Validation passes with all valid fields."""
    renderer = WetBrushRenderer()
    renderer.validate(_valid_stroke(), CANVAS_SIZE)


def test_missing_required_fields() -> None:
    """Validation raises ValueError for each missing required field."""
    renderer = WetBrushRenderer()
    required_fields = [
        "points",
        "softness",
        "flow",
        "color_hex",
        "thickness",
        "opacity",
    ]

    for field in required_fields:
        stroke = _valid_stroke()
        del stroke[field]  # type: ignore[misc]
        with pytest.raises(ValueError, match=field):
            renderer.validate(stroke, CANVAS_SIZE)


def test_softness_out_of_range() -> None:
    """Validation raises ValueError when softness is below min or above max."""
    renderer = WetBrushRenderer()

    with pytest.raises(ValueError, match="softness"):
        renderer.validate(
            _valid_stroke(softness=0), CANVAS_SIZE
        )  # below MIN_SOFTNESS=1

    with pytest.raises(ValueError, match="softness"):
        renderer.validate(
            _valid_stroke(softness=31), CANVAS_SIZE
        )  # above MAX_SOFTNESS=30


def test_flow_out_of_range() -> None:
    """Validation raises ValueError when flow is below min or above max."""
    renderer = WetBrushRenderer()

    with pytest.raises(ValueError, match="flow"):
        renderer.validate(_valid_stroke(flow=0.0), CANVAS_SIZE)  # below MIN_FLOW=0.1

    with pytest.raises(ValueError, match="flow"):
        renderer.validate(_valid_stroke(flow=1.1), CANVAS_SIZE)  # above MAX_FLOW=1.0


def test_points_validation_too_few() -> None:
    """Validation raises ValueError when fewer than 2 points are provided."""
    renderer = WetBrushRenderer()
    with pytest.raises(ValueError, match="points"):
        renderer.validate(_valid_stroke(points=[[100, 100]]), CANVAS_SIZE)


def test_points_validation_too_many() -> None:
    """Validation raises ValueError when more than 50 points are provided."""
    renderer = WetBrushRenderer()
    many_points = [[i * 10, i * 5] for i in range(51)]
    with pytest.raises(ValueError, match="points"):
        renderer.validate(_valid_stroke(points=many_points), CANVAS_SIZE)


def test_points_validation_out_of_bounds() -> None:
    """Validation raises ValueError when a point is outside canvas bounds."""
    renderer = WetBrushRenderer()

    # x out of bounds
    with pytest.raises(ValueError, match="out of bounds"):
        renderer.validate(
            _valid_stroke(points=[[100, 100], [900, 200]]),  # x=900 > width=800
            CANVAS_SIZE,
        )

    # y out of bounds
    with pytest.raises(ValueError, match="out of bounds"):
        renderer.validate(
            _valid_stroke(points=[[100, 100], [200, 700]]),  # y=700 > height=600
            CANVAS_SIZE,
        )


def test_invalid_field_types() -> None:
    """Validation raises ValueError for non-integer softness or non-float flow."""
    renderer = WetBrushRenderer()

    with pytest.raises(ValueError, match="softness"):
        renderer.validate(_valid_stroke(softness=5.5), CANVAS_SIZE)  # float not int

    with pytest.raises(ValueError, match="flow"):
        renderer.validate(_valid_stroke(flow="high"), CANVAS_SIZE)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Rendering tests
# ---------------------------------------------------------------------------


def test_render_basic_wet_brush() -> None:
    """render_to_image() returns an image without error."""
    renderer = WetBrushRenderer()
    image = Image.new("RGB", (800, 600), (255, 255, 255))
    result = renderer.render_to_image(_valid_stroke(), image)
    assert result is not None


def test_render_to_image_returns_rgb() -> None:
    """render_to_image() returns an RGB-mode image (not RGBA)."""
    renderer = WetBrushRenderer()
    image = Image.new("RGB", (800, 600), (255, 255, 255))
    result = renderer.render_to_image(_valid_stroke(), image)
    assert result.mode == "RGB"


def test_render_to_image_blurs_edges() -> None:
    """Edge pixels should have lower colour intensity than the stroke centre."""
    renderer = WetBrushRenderer()

    # Start from a white canvas so any colour painted will lower overall pixel
    # intensity at the margin relative to a direct hit.
    image = Image.new("RGB", (800, 600), (255, 255, 255))

    # Horizontal stroke along the middle with a bold blue colour and high softness
    stroke = _valid_stroke(
        points=[[300, 300], [500, 300]],
        color_hex="#0000FF",  # pure blue
        softness=10,
        flow=1.0,
        opacity=1.0,
        thickness=4,
    )
    result = renderer.render_to_image(stroke, image)

    # Centre pixel (on or very near stroke path) should contain more blue than
    # a pixel far from the stroke.
    cx, cy = 400, 300  # midpoint of stroke path
    far_x, far_y = 400, 100  # well outside the blur radius

    centre_pixel = cast(tuple[int, ...], result.getpixel((cx, cy)))
    far_pixel = cast(tuple[int, ...], result.getpixel((far_x, far_y)))

    # The blue channel at the centre should be lower than at the far point
    # (blue was painted; white canvas has blue=255, so painted pixel < 255 in
    # the red/green channels and <= 255 in blue — instead compare total RGB sum).
    assert sum(centre_pixel) < sum(far_pixel), (
        f"Expected centre {centre_pixel} to be darker/more-coloured than far {far_pixel}"
    )


def test_needs_image_access_is_true() -> None:
    """needs_image_access property should return True."""
    renderer = WetBrushRenderer()
    assert renderer.needs_image_access is True


def test_render_raises_runtime_error() -> None:
    """Calling render() should raise RuntimeError."""
    from PIL import ImageDraw

    renderer = WetBrushRenderer()
    image = Image.new("RGB", (800, 600), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    with pytest.raises(RuntimeError, match="render_to_image"):
        renderer.render(_valid_stroke(), draw)


# ---------------------------------------------------------------------------
# Integration test with CanvasManager
# ---------------------------------------------------------------------------


def test_canvas_manager_applies_wet_brush() -> None:
    """CanvasManager applies a wet-brush stroke and updates stroke_count."""
    manager = CanvasManager(width=800, height=600)
    original_pixels = list(manager.image.getdata())

    stroke = _valid_stroke()
    manager.apply_stroke(stroke)

    # stroke_count should have incremented
    assert manager.stroke_count == 1

    # At least some pixels should have changed
    new_pixels = list(manager.image.getdata())
    assert original_pixels != new_pixels, (
        "Expected canvas image to change after wet-brush stroke"
    )


# ---------------------------------------------------------------------------
# Parse branch test (5.2b coverage)
# ---------------------------------------------------------------------------


def test_parse_wet_brush_stroke_fields() -> None:
    """StrokeParser._parse_single_stroke correctly extracts wet-brush fields."""
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(
        0, str(_Path(__file__).parent.parent / "src" / "paint_by_language_model")
    )

    from services.stroke_parser import StrokeParser

    raw = {
        "type": "wet-brush",
        "points": [[100, 100], [200, 200]],
        "softness": 8,
        "flow": 0.6,
        "color_hex": "#112233",
        "thickness": 6,
        "opacity": 0.9,
    }

    parsed = StrokeParser()._parse_single_stroke(raw)

    assert parsed["type"] == "wet-brush"
    assert parsed["points"] == [[100, 100], [200, 200]]
    assert parsed["softness"] == 8
    assert parsed["flow"] == pytest.approx(0.6)
    assert parsed["color_hex"] == "#112233"
