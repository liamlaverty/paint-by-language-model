"""Arc renderer for drawing elliptical arcs on canvas."""

import logging
import re
from typing import TYPE_CHECKING

from config import MAX_ARC_ANGLE

from .base_renderer import StrokeRenderer

if TYPE_CHECKING:
    from PIL import ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class ArcRenderer(StrokeRenderer):
    """
    Renderer for drawing elliptical arcs.

    Handles arc drawing with support for bounding boxes, angles, color, thickness, and opacity.
    Uses PIL's ImageDraw.arc() method with RGBA color composition for transparency.
    """

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that an arc stroke has all required fields and valid values.

        Args:
            stroke (Stroke): The stroke data to validate
            canvas_size (tuple[int, int]): Canvas dimensions as (width, height)

        Raises:
            ValueError: If stroke validation fails (missing fields, out of bounds, etc.)
        """
        width, height = canvas_size

        # Check required fields exist
        required_fields = [
            "arc_bbox",
            "arc_start_angle",
            "arc_end_angle",
            "color_hex",
            "thickness",
            "opacity",
        ]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Arc stroke missing required field: {field}")

        # Validate bounding box
        arc_bbox = stroke["arc_bbox"]
        if arc_bbox is None:
            raise ValueError("Arc stroke requires arc_bbox")

        # Check bbox format - should be list/tuple of 4 integers
        if not isinstance(arc_bbox, (list, tuple)) or len(arc_bbox) != 4:
            raise ValueError(
                f"arc_bbox must be a list/tuple of 4 integers [x0, y0, x1, y1], got {type(arc_bbox).__name__} with length {len(arc_bbox) if isinstance(arc_bbox, (list, tuple)) else 'N/A'}"
            )

        x0, y0, x1, y1 = arc_bbox

        # Ensure all bbox coordinates are integers
        if not all(isinstance(coord, int) for coord in [x0, y0, x1, y1]):
            coord_types = [type(coord).__name__ for coord in [x0, y0, x1, y1]]
            raise ValueError(f"All arc_bbox coordinates must be integers, got {coord_types}")

        # Check bounding box logic
        if x0 >= x1:
            raise ValueError(f"Invalid arc_bbox: x0 ({x0}) must be less than x1 ({x1})")
        if y0 >= y1:
            raise ValueError(f"Invalid arc_bbox: y0 ({y0}) must be less than y1 ({y1})")

        # Check coordinates are within canvas bounds
        if not (0 <= x0 < width):
            raise ValueError(f"arc_bbox x0 {x0} out of bounds [0, {width})")
        if not (0 <= y0 < height):
            raise ValueError(f"arc_bbox y0 {y0} out of bounds [0, {height})")
        if not (0 <= x1 < width):
            raise ValueError(f"arc_bbox x1 {x1} out of bounds [0, {width})")
        if not (0 <= y1 < height):
            raise ValueError(f"arc_bbox y1 {y1} out of bounds [0, {height})")

        # Validate angles
        arc_start_angle = stroke["arc_start_angle"]
        arc_end_angle = stroke["arc_end_angle"]

        if arc_start_angle is None:
            raise ValueError("Arc stroke requires arc_start_angle")
        if arc_end_angle is None:
            raise ValueError("Arc stroke requires arc_end_angle")

        # Ensure angles are integers
        if not isinstance(arc_start_angle, int):
            raise ValueError(
                f"arc_start_angle must be an integer, got {type(arc_start_angle).__name__}"
            )
        if not isinstance(arc_end_angle, int):
            raise ValueError(
                f"arc_end_angle must be an integer, got {type(arc_end_angle).__name__}"
            )

        # Check angle ranges
        if not (0 <= arc_start_angle <= MAX_ARC_ANGLE):
            raise ValueError(f"arc_start_angle {arc_start_angle} out of range [0, {MAX_ARC_ANGLE}]")
        if not (0 <= arc_end_angle <= MAX_ARC_ANGLE):
            raise ValueError(f"arc_end_angle {arc_end_angle} out of range [0, {MAX_ARC_ANGLE}]")

        # Validate color format (hex pattern #RRGGBB or #RRGGBBAA)
        color_hex = stroke["color_hex"]
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
        if not hex_pattern.match(color_hex):
            raise ValueError(
                f"Invalid hex color format: {color_hex} (expected #RRGGBB or #RRGGBBAA)"
            )

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

        logger.debug(
            f"Arc stroke validated: bbox={arc_bbox}, angles={arc_start_angle}°-{arc_end_angle}°"
        )

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Render an arc stroke onto the canvas using the provided ImageDraw object.

        Args:
            stroke (Stroke): The stroke data containing arc bbox, angles, color, and style
            draw (ImageDraw.ImageDraw): PIL ImageDraw object for drawing operations

        Raises:
            ValueError: If stroke data is invalid or incomplete
        """
        # Extract arc parameters
        arc_bbox = stroke["arc_bbox"]
        arc_start_angle = stroke["arc_start_angle"]
        arc_end_angle = stroke["arc_end_angle"]

        if arc_bbox is None:
            raise ValueError("Arc stroke requires arc_bbox")
        if arc_start_angle is None:
            raise ValueError("Arc stroke requires arc_start_angle")
        if arc_end_angle is None:
            raise ValueError("Arc stroke requires arc_end_angle")

        # Convert list to tuple for PIL
        bbox_tuple = tuple(arc_bbox)

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

        # Draw arc
        thickness = stroke["thickness"]
        draw.arc(
            bbox_tuple,
            start=arc_start_angle,
            end=arc_end_angle,
            fill=color_rgba,
            width=thickness,
        )

        logger.debug(
            f"Rendered arc: bbox={arc_bbox}, angles={arc_start_angle}°-{arc_end_angle}°, "
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
