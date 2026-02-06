"""Stroke renderer package for canvas drawing operations."""

from .arc_renderer import ArcRenderer
from .base_renderer import StrokeRenderer, StrokeRendererFactory
from .line_renderer import LineRenderer

# Register renderers with factory on module import
StrokeRendererFactory.register_renderer("line", LineRenderer)
StrokeRendererFactory.register_renderer("arc", ArcRenderer)

__all__ = ["StrokeRenderer", "StrokeRendererFactory", "LineRenderer", "ArcRenderer"]
