"""Stroke renderer package for canvas drawing operations."""

from .arc_renderer import ArcRenderer
from .base_renderer import StrokeRenderer, StrokeRendererFactory
from .burn_renderer import BurnRenderer
from .chalk_renderer import ChalkRenderer
from .circle_renderer import CircleRenderer
from .dodge_renderer import DodgeRenderer
from .dry_brush_renderer import DryBrushRenderer
from .line_renderer import LineRenderer
from .polyline_renderer import PolylineRenderer
from .renderer_utils import (
    hex_to_rgb,
    hex_to_rgba,
    stroke_color_to_rgba,
    validate_color_hex,
    validate_common_stroke_fields,
    validate_opacity,
    validate_thickness,
)
from .splatter_renderer import SplatterRenderer
from .wet_brush_renderer import WetBrushRenderer

# Register renderers with factory on module import
StrokeRendererFactory.register_renderer("line", LineRenderer)
StrokeRendererFactory.register_renderer("arc", ArcRenderer)
StrokeRendererFactory.register_renderer("polyline", PolylineRenderer)
StrokeRendererFactory.register_renderer("circle", CircleRenderer)
StrokeRendererFactory.register_renderer("splatter", SplatterRenderer)
StrokeRendererFactory.register_renderer("dry-brush", DryBrushRenderer)
StrokeRendererFactory.register_renderer("chalk", ChalkRenderer)
StrokeRendererFactory.register_renderer("wet-brush", WetBrushRenderer)
StrokeRendererFactory.register_renderer("burn", BurnRenderer)
StrokeRendererFactory.register_renderer("dodge", DodgeRenderer)

__all__ = [
    "StrokeRenderer",
    "StrokeRendererFactory",
    "LineRenderer",
    "ArcRenderer",
    "PolylineRenderer",
    "CircleRenderer",
    "SplatterRenderer",
    "DryBrushRenderer",
    "ChalkRenderer",
    "WetBrushRenderer",
    "BurnRenderer",
    "DodgeRenderer",
    "hex_to_rgb",
    "hex_to_rgba",
    "stroke_color_to_rgba",
    "validate_color_hex",
    "validate_common_stroke_fields",
    "validate_opacity",
    "validate_thickness",
]
