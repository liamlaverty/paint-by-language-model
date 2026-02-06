"""Line renderer for drawing straight lines on canvas."""

import logging
import re
from typing import TYPE_CHECKING

from .base_renderer import StrokeRenderer

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
        required_fields = ["start_x", "start_y", "end_x", "end_y", "color_hex", "thickness", "opacity"]
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
        if not (0 <= start_x < width):
            raise ValueError(f"start_x {start_x} out of bounds [0, {width})")
        if not (0 <= start_y < height):
            raise ValueError(f"start_y {start_y} out of bounds [0, {height})")
        if not (0 <= end_x < width):
            raise ValueError(f"end_x {end_x} out of bounds [0, {width})")
        if not (0 <= end_y < height):
            raise ValueError(f"end_y {end_y} out of bounds [0, {height})")

        # Validate color format (hex pattern #RRGGBB or #RRGGBBAA)
        color_hex = stroke["color_hex"]
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
        if not hex_pattern.match(color_hex):
            raise ValueError(f"Invalid hex color format: {color_hex} (expected #RRGGBB or #RRGGBBAA)")

        # Validate thickness
        thickness = stroke["thickness"]
        if not isinstance(thickness, int):
            raise ValueError(f"thickness must be an integer, got {type(thickness).__name__}")
        if not (1 <= thickness <= 50):
            raise ValueError(f"thickness {thickness} out of range [1, 50]")

        # Validate opacity
        opacity = stroke["opacity"]
        if not isinstance(opacity, (int, float)):
            raise ValueError(f"opacity must be a number, got {type(opacity).__name__}")
        if not (0.0 <= opacity <= 1.0):
            raise ValueError(f"opacity {opacity} out of range [0.0, 1.0]")

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

        # Convert hex color to RGBA tuple
        # Handle both 6-digit (#RRGGBB) and 8-digit (#RRGGBBAA) formats
        hex_color = stroke["color_hex"]
        opacity = stroke["opacity"]

        if len(hex_color) == 9:  # #RRGGBBAA format (8 hex digits + #)
            color_rgba = self._hex_to_rgba(hex_color)
            # VLM-provided alpha overrides opacity field for 8-digit colors
        else:  # #RRGGBB format (6 hex digits + #)
            color_rgb = self._hex_to_rgb(hex_color)
            # Apply opacity by converting to RGBA (alpha channel)
            alpha = int(opacity * 255)
            color_rgba = color_rgb + (alpha,)

        # Draw line
        thickness = stroke["thickness"]
        draw.line(
            [(start_x, start_y), (end_x, end_y)],
            fill=color_rgba,
            width=thickness,
        )

        logger.debug(
            f"Rendered line: ({start_x},{start_y}) to ({end_x},{end_y}), "
            f"color={stroke['color_hex']}, thickness={thickness}, opacity={opacity}"
        )

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """
        Convert 6-digit hex color string to RGB tuple.

        Args:
            hex_color (str): Hex color string (e.g., "#FF5733")

        Returns:
            tuple[int, int, int]: RGB tuple (e.g., (255, 87, 51))
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)

    def _hex_to_rgba(self, hex_color: str) -> tuple[int, int, int, int]:
        """
        Convert 8-digit hex color string to RGBA tuple.

        Args:
            hex_color (str): Hex color string with alpha (e.g., "#FF5733CC")

        Returns:
            tuple[int, int, int, int]: RGBA tuple (e.g., (255, 87, 51, 204))
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(hex_color[6:8], 16)
        return (r, g, b, a)
