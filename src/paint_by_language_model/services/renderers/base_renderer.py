"""Base renderer class and factory for stroke rendering."""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class StrokeRenderer(ABC):
    """
    Abstract base class for stroke renderers.

    Defines the interface for rendering different stroke types on a canvas.
    Each stroke type (line, arc, polyline, etc.) should implement this interface.
    """

    @abstractmethod
    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Render a stroke onto the canvas using the provided ImageDraw object.

        Args:
            stroke (Stroke): The stroke data containing position, color, and type-specific params
            draw (ImageDraw.ImageDraw): PIL ImageDraw object for drawing operations

        Raises:
            ValueError: If stroke data is invalid or incomplete
        """
        pass

    @abstractmethod
    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a stroke is valid for the given canvas size.

        Args:
            stroke (Stroke): The stroke data to validate
            canvas_size (tuple[int, int]): Canvas dimensions as (width, height)

        Raises:
            ValueError: If stroke validation fails (missing fields, out of bounds, etc.)
        """
        pass


class StrokeRendererFactory:
    """
    Factory for creating stroke renderer instances.

    Uses the Strategy Pattern to return the appropriate renderer for each stroke type.
    """

    # Registry of stroke type to renderer class mappings
    # Will be populated as renderer implementations are created
    _renderers: dict[str, type[StrokeRenderer]] = {}

    @classmethod
    def register_renderer(cls, stroke_type: str, renderer_class: type[StrokeRenderer]) -> None:
        """
        Register a renderer class for a specific stroke type.

        Args:
            stroke_type (str): The stroke type identifier (e.g., "line", "arc")
            renderer_class (type[StrokeRenderer]): The renderer class to register

        Raises:
            ValueError: If stroke_type is already registered
        """
        if stroke_type in cls._renderers:
            logger.warning(f"Overwriting existing renderer for stroke type: {stroke_type}")
        cls._renderers[stroke_type] = renderer_class
        logger.debug(f"Registered {renderer_class.__name__} for stroke type '{stroke_type}'")

    @classmethod
    def get_renderer(cls, stroke_type: str) -> StrokeRenderer:
        """
        Get a renderer instance for the specified stroke type.

        Args:
            stroke_type (str): The type of stroke to render (e.g., "line", "arc", "circle")

        Returns:
            StrokeRenderer: An instance of the appropriate renderer

        Raises:
            ValueError: If the stroke type is not supported
        """
        if stroke_type not in cls._renderers:
            supported_types = ", ".join(sorted(cls._renderers.keys()))
            raise ValueError(
                f"Unsupported stroke type: '{stroke_type}'. "
                f"Supported types: {supported_types if supported_types else 'none registered'}"
            )

        renderer_class = cls._renderers[stroke_type]
        return renderer_class()
