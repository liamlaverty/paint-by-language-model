"""Line renderer for drawing straight lines on canvas."""

import logging
from typing import TYPE_CHECKING

from .base_renderer import StrokeRenderer
from .renderer_utils import stroke_color_to_rgba, validate_common_stroke_fields

if TYPE_CHECKING:
    from PIL import ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class LineRenderer(StrokeRenderer):
    """
    Renderer for drawing straight lines.

    Handles line drawing with support for color, thickness, and opacity.
    Uses PIL's ImageDraw.line() method with RGBA color composition for transparency.
    """

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a line stroke has all required fields and valid values.

        Args:
            stroke (Stroke): The stroke data to validate
            canvas_size (tuple[int, int]): Canvas dimensions as (width, height)

        Raises:
            ValueError: If stroke validation fails (missing fields, out of bounds, etc.)
        """
        width, height = canvas_size

        # Check required fields exist
        required_fields = [
            "start_x",
            "start_y",
            "end_x",
            "end_y",
            "color_hex",
            "thickness",
            "opacity",
        ]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Line stroke missing required field: {field}")

        # Validate coordinate types and values
        start_x = stroke["start_x"]
        start_y = stroke["start_y"]
        end_x = stroke.get("end_x")
        end_y = stroke.get("end_y")

        if end_x is None or end_y is None:
            raise ValueError("Line stroke requires end_x and end_y")

        # Ensure coordinates are integers
        if not isinstance(start_x, int):
            raise ValueError(f"start_x must be an integer, got {type(start_x).__name__}")
        if not isinstance(start_y, int):
            raise ValueError(f"start_y must be an integer, got {type(start_y).__name__}")
        if not isinstance(end_x, int):
            raise ValueError(f"end_x must be an integer, got {type(end_x).__name__}")
        if not isinstance(end_y, int):
            raise ValueError(f"end_y must be an integer, got {type(end_y).__name__}")

        # Check coordinates are within canvas bounds
        # Allow x == width and y == height (LLMs use canvas dimensions as the far-edge
        # coordinate; PIL clips rendering to canvas bounds automatically).
        if not (0 <= start_x <= width):
            raise ValueError(f"start_x {start_x} out of bounds [0, {width}]")
        if not (0 <= start_y <= height):
            raise ValueError(f"start_y {start_y} out of bounds [0, {height}]")
        if not (0 <= end_x <= width):
            raise ValueError(f"end_x {end_x} out of bounds [0, {width}]")
        if not (0 <= end_y <= height):
            raise ValueError(f"end_y {end_y} out of bounds [0, {height}]")

        # Validate common stroke fields (color, thickness, opacity)
        validate_common_stroke_fields(stroke)

        logger.debug(f"Line stroke validated: ({start_x},{start_y}) to ({end_x},{end_y})")

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Render a line stroke onto the canvas using the provided ImageDraw object.

        Args:
            stroke (Stroke): The stroke data containing line position, color, and style
            draw (ImageDraw.ImageDraw): PIL ImageDraw object for drawing operations

        Raises:
            ValueError: If stroke data is invalid or incomplete
        """
        # Extract line coordinates
        start_x = stroke["start_x"]
        start_y = stroke["start_y"]
        end_x = stroke.get("end_x")
        end_y = stroke.get("end_y")

        if end_x is None or end_y is None:
            raise ValueError("Line stroke requires end_x and end_y")

        # Convert hex color to RGBA tuple with opacity
        color_rgba = stroke_color_to_rgba(stroke["color_hex"], stroke["opacity"])

        # Draw line
        thickness = stroke["thickness"]
        draw.line(
            [(start_x, start_y), (end_x, end_y)],
            fill=color_rgba,
            width=thickness,
        )

        logger.debug(
            f"Rendered line: ({start_x},{start_y}) to ({end_x},{end_y}), "
            f"color={stroke['color_hex']}, thickness={thickness}, opacity={stroke['opacity']}"
        )
