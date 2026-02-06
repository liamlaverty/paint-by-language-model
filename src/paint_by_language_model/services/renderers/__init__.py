"""Stroke renderer package for canvas drawing operations."""

from .arc_renderer import ArcRenderer
from .base_renderer import StrokeRenderer, StrokeRendererFactory
from .line_renderer import LineRenderer
from .renderer_utils import (
    hex_to_rgb,
    hex_to_rgba,
    stroke_color_to_rgba,
    validate_color_hex,
    validate_common_stroke_fields,
    validate_opacity,
    validate_thickness,
)

# Register renderers with factory on module import
StrokeRendererFactory.register_renderer("line", LineRenderer)
StrokeRendererFactory.register_renderer("arc", ArcRenderer)

__all__ = [
    "StrokeRenderer",
    "StrokeRendererFactory",
    "LineRenderer",
    "ArcRenderer",
    "hex_to_rgb",
    "hex_to_rgba",
    "stroke_color_to_rgba",
    "validate_color_hex",
    "validate_common_stroke_fields",
    "validate_opacity",
    "validate_thickness",
]
