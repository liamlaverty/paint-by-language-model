"""Comprehensive tests for DodgeRenderer implementation."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

import pytest  # noqa: E402
from models.stroke import Stroke  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from services.canvas_manager import CanvasManager  # noqa: E402
from services.renderers import DodgeRenderer, StrokeRendererFactory  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_stroke(**overrides: object) -> "Stroke":
    """Return a minimal valid dodge stroke, allowing field overrides.

    Args:
        **overrides (object): Field overrides to apply to the base stroke.

    Returns:
        Stroke: A valid dodge stroke dict with optional field overrides.
    """
    base: Stroke = {
        "type": "dodge",
        "center_x": 200,
        "center_y": 150,
        "radius": 60,
        "intensity": 0.5,
        "color_hex": "#ffffff",
        "thickness": 1,
        "opacity": 1.0,
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


CANVAS_SIZE = (400, 300)


# ---------------------------------------------------------------------------
# Factory registration
# ---------------------------------------------------------------------------


def test_factory_registration() -> None:
    """DodgeRenderer is registered in StrokeRendererFactory."""
    renderer = StrokeRendererFactory.get_renderer("dodge")
    assert isinstance(renderer, DodgeRenderer)


# ---------------------------------------------------------------------------
# needs_image_access
# ---------------------------------------------------------------------------


def test_needs_image_access_is_true() -> None:
    """DodgeRenderer.needs_image_access returns True."""
    renderer = DodgeRenderer()
    assert renderer.needs_image_access is True


# ---------------------------------------------------------------------------
# render() raises RuntimeError
# ---------------------------------------------------------------------------


def test_render_raises_runtime_error() -> None:
    """Calling render() on DodgeRenderer raises RuntimeError."""
    renderer = DodgeRenderer()
    canvas = Image.new("RGB", CANVAS_SIZE, "white")
    draw = ImageDraw.Draw(canvas)
    with pytest.raises(RuntimeError, match="render_to_image"):
        renderer.render(_valid_stroke(), draw)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_valid_dodge_stroke() -> None:
    """Validation passes with all valid fields."""
    renderer = DodgeRenderer()
    renderer.validate(_valid_stroke(), CANVAS_SIZE)


def test_missing_required_fields() -> None:
    """Validation raises ValueError for each missing required field."""
    renderer = DodgeRenderer()
    required_fields = [
        "center_x",
        "center_y",
        "radius",
        "intensity",
        "color_hex",
        "thickness",
        "opacity",
    ]

    for field in required_fields:
        stroke = _valid_stroke()
        del stroke[field]  # type: ignore[misc]
        with pytest.raises(ValueError, match=field):
            renderer.validate(stroke, CANVAS_SIZE)


def test_radius_out_of_range() -> None:
    """Validation raises ValueError when radius is outside allowed range."""
    renderer = DodgeRenderer()

    with pytest.raises(ValueError, match="radius"):
        renderer.validate(
            _valid_stroke(radius=4), CANVAS_SIZE
        )  # below MIN_BURN_DODGE_RADIUS=5

    with pytest.raises(ValueError, match="radius"):
        renderer.validate(
            _valid_stroke(radius=301), CANVAS_SIZE
        )  # above MAX_BURN_DODGE_RADIUS=300


def test_intensity_out_of_range() -> None:
    """Validation raises ValueError when intensity is outside allowed range."""
    renderer = DodgeRenderer()

    with pytest.raises(ValueError, match="intensity"):
        renderer.validate(_valid_stroke(intensity=0.01), CANVAS_SIZE)  # below MIN=0.05

    with pytest.raises(ValueError, match="intensity"):
        renderer.validate(_valid_stroke(intensity=0.9), CANVAS_SIZE)  # above MAX=0.8


def test_center_out_of_bounds() -> None:
    """Validation raises ValueError when center is outside canvas dimensions."""
    renderer = DodgeRenderer()
    width, height = CANVAS_SIZE

    with pytest.raises(ValueError, match="center_x"):
        renderer.validate(_valid_stroke(center_x=width + 1), CANVAS_SIZE)

    with pytest.raises(ValueError, match="center_y"):
        renderer.validate(_valid_stroke(center_y=height + 1), CANVAS_SIZE)


def test_invalid_field_types() -> None:
    """Validation raises ValueError for non-integer radius or non-float intensity."""
    renderer = DodgeRenderer()

    with pytest.raises(ValueError, match="radius"):
        renderer.validate(_valid_stroke(radius=50.5), CANVAS_SIZE)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="intensity"):
        renderer.validate(_valid_stroke(intensity=1), CANVAS_SIZE)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Rendering tests
# ---------------------------------------------------------------------------


def test_render_basic_dodge() -> None:
    """Dodge on a dark canvas lightens centre pixels."""
    renderer = DodgeRenderer()
    # Use a dark uniform canvas so lightening is measurable
    canvas = Image.new("RGB", CANVAS_SIZE, (50, 50, 50))
    cx, cy = 200, 150
    stroke = _valid_stroke(center_x=cx, center_y=cy, radius=50, intensity=0.7)

    before = canvas.getpixel((cx, cy))
    result = renderer.render_to_image(stroke, canvas)
    after = result.getpixel((cx, cy))

    # Center pixel must be lighter
    assert after[0] > before[0], f"Expected red channel to lighten: {before} → {after}"


def test_render_on_black_canvas() -> None:
    """Dodge on a black canvas lightens the centre (screen blend of bright with black lifts to bright)."""
    renderer = DodgeRenderer()
    canvas = Image.new("RGB", CANVAS_SIZE, (0, 0, 0))
    cx, cy = 200, 150
    stroke = _valid_stroke(center_x=cx, center_y=cy, radius=50, intensity=0.6)

    result = renderer.render_to_image(stroke, canvas)
    after = result.getpixel((cx, cy))

    assert after[0] > 0, (
        f"Expected centre pixel to be lighter than 0 on black canvas, got {after}"
    )


def test_render_edge_untouched() -> None:
    """Pixels outside the dodge radius are unchanged."""
    renderer = DodgeRenderer()
    canvas = Image.new("RGB", CANVAS_SIZE, (80, 80, 80))
    cx, cy, radius = 200, 150, 40
    stroke = _valid_stroke(center_x=cx, center_y=cy, radius=radius)

    # Pick a pixel well outside the radius
    px, py = cx + radius + 20, cy
    before = canvas.getpixel((px, py))
    result = renderer.render_to_image(stroke, canvas)
    after = result.getpixel((px, py))

    assert after == before, (
        f"Pixel outside radius should be unchanged: {before} → {after}"
    )


def test_render_intensity_scales_lightening() -> None:
    """Higher intensity produces lighter centre pixels than lower intensity."""
    renderer = DodgeRenderer()
    cx, cy, radius = 200, 150, 60

    canvas_low = Image.new("RGB", CANVAS_SIZE, (80, 80, 80))
    stroke_low = _valid_stroke(center_x=cx, center_y=cy, radius=radius, intensity=0.1)
    result_low = renderer.render_to_image(stroke_low, canvas_low)

    canvas_high = Image.new("RGB", CANVAS_SIZE, (80, 80, 80))
    stroke_high = _valid_stroke(center_x=cx, center_y=cy, radius=radius, intensity=0.8)
    result_high = renderer.render_to_image(stroke_high, canvas_high)

    low_pixel = result_low.getpixel((cx, cy))
    high_pixel = result_high.getpixel((cx, cy))

    assert high_pixel[0] > low_pixel[0], (
        f"Higher intensity should produce lighter pixel: low={low_pixel}, high={high_pixel}"
    )


# ---------------------------------------------------------------------------
# CanvasManager integration
# ---------------------------------------------------------------------------


def test_canvas_manager_applies_dodge() -> None:
    """CanvasManager.apply_stroke() correctly applies a dodge stroke."""
    canvas = CanvasManager(width=400, height=300, background_color=(80, 80, 80))
    cx, cy, radius = 200, 150, 50
    stroke = _valid_stroke(center_x=cx, center_y=cy, radius=radius, intensity=0.6)

    # Capture pixel before
    before = canvas.image.getpixel((cx, cy))

    canvas.apply_stroke(stroke)

    # Pixel should be lighter after dodge
    after = canvas.image.getpixel((cx, cy))
    assert after[0] > before[0], (
        f"CanvasManager dodge should lighten pixel: {before} → {after}"
    )


# ---------------------------------------------------------------------------
# Parse branch test (stroke_vlm_client)
# ---------------------------------------------------------------------------


def test_parse_dodge_stroke_branch() -> None:
    """_parse_single_stroke correctly parses a raw dodge stroke dict."""
    sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))
    from services.stroke_vlm_client import StrokeVLMClient  # noqa: F401

    raw: dict[str, object] = {
        "type": "dodge",
        "center_x": 150,
        "center_y": 100,
        "radius": 40,
        "intensity": 0.5,
        "color_hex": "#ffffff",
        "thickness": 1,
        "opacity": 1.0,
        "reasoning": "highlighting",
    }

    # Access the private method via name mangling workaround
    client = StrokeVLMClient.__new__(StrokeVLMClient)
    parsed = client._parse_single_stroke(raw)  # type: ignore[attr-defined]

    assert parsed["center_x"] == 150
    assert parsed["center_y"] == 100
    assert parsed["radius"] == 40
    assert parsed["intensity"] == 0.5
    assert parsed["type"] == "dodge"
