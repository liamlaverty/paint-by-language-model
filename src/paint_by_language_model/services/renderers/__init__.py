"""Stroke renderer package for canvas drawing operations."""

from .base_renderer import StrokeRenderer, StrokeRendererFactory
from .line_renderer import LineRenderer

# Register renderers with factory on module import
StrokeRendererFactory.register_renderer("line", LineRenderer)

__all__ = ["StrokeRenderer", "StrokeRendererFactory", "LineRenderer"]
