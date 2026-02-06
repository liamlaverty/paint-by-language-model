"""Polyline renderer for drawing connected multi-point lines on canvas."""

import logging
from typing import TYPE_CHECKING

from config import MAX_POLYLINE_POINTS, MIN_POLYLINE_POINTS

from .base_renderer import StrokeRenderer
from .renderer_utils import stroke_color_to_rgba, validate_common_stroke_fields

if TYPE_CHECKING:
    from PIL import ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class PolylineRenderer(StrokeRenderer):
    """
    Renderer for drawing connected multi-point lines (polylines).

    Handles polyline drawing with support for color, thickness, and opacity.
    Uses PIL's ImageDraw.line() method with a list of points to create organic,
    freeform stroke shapes.
    """

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a polyline stroke has all required fields and valid values.

        Args:
            stroke (Stroke): The stroke data to validate
            canvas_size (tuple[int, int]): Canvas dimensions as (width, height)

        Raises:
            ValueError: If stroke validation fails (missing fields, out of bounds, etc.)
        """
        width, height = canvas_size

        # Check required field exists
        if "points" not in stroke:
            raise ValueError("Polyline stroke missing required field: points")

        points = stroke["points"]

        # Validate points format
        if not isinstance(points, list):
            raise ValueError(f"points must be a list, got {type(points).__name__}")

        # Check minimum/maximum number of points
        if len(points) < MIN_POLYLINE_POINTS:
            raise ValueError(
                f"Polyline must have at least {MIN_POLYLINE_POINTS} points, got {len(points)}"
            )

        if len(points) > MAX_POLYLINE_POINTS:
            raise ValueError(
                f"Polyline cannot have more than {MAX_POLYLINE_POINTS} points, got {len(points)}"
            )

        # Validate each point
        for i, point in enumerate(points):
            # Check point is a list/tuple of length 2
            if not isinstance(point, (list, tuple)):
                raise ValueError(f"Point {i} must be a list or tuple, got {type(point).__name__}")

            if len(point) != 2:
                raise ValueError(f"Point {i} must have exactly 2 coordinates, got {len(point)}")

            x, y = point

            # Check coordinates are integers
            if not isinstance(x, int):
                raise ValueError(
                    f"Point {i} x-coordinate must be an integer, got {type(x).__name__}"
                )
            if not isinstance(y, int):
                raise ValueError(
                    f"Point {i} y-coordinate must be an integer, got {type(y).__name__}"
                )

            # Check coordinates are within canvas bounds
            if not (0 <= x < width):
                raise ValueError(f"Point {i} x-coordinate {x} out of bounds [0, {width})")
            if not (0 <= y < height):
                raise ValueError(f"Point {i} y-coordinate {y} out of bounds [0, {height})")

        # Validate common stroke fields (color, thickness, opacity)
        validate_common_stroke_fields(stroke)

        logger.debug(f"Polyline stroke validated: {len(points)} points")

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Render a polyline stroke onto the canvas using the provided ImageDraw object.

        Args:
            stroke (Stroke): The stroke data containing polyline points, color, and style
            draw (ImageDraw.ImageDraw): PIL ImageDraw object for drawing operations

        Raises:
            ValueError: If stroke data is invalid or incomplete
        """
        # Extract points list
        points = stroke.get("points")

        if points is None:
            raise ValueError("Polyline stroke requires points field")

        # Convert list of [x, y] pairs to list of (x, y) tuples for PIL
        points_tuples = [(int(x), int(y)) for x, y in points]

        # Convert hex color to RGBA tuple with opacity
        color_rgba = stroke_color_to_rgba(stroke["color_hex"], stroke["opacity"])

        # Draw polyline
        thickness = stroke["thickness"]
        draw.line(
            points_tuples,
            fill=color_rgba,
            width=thickness,
        )

        logger.debug(
            f"Rendered polyline: {len(points)} points, "
            f"color={stroke['color_hex']}, thickness={thickness}, opacity={stroke['opacity']}"
        )
