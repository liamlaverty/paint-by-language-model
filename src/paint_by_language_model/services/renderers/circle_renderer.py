"""Circle renderer for drawing circles and ellipses on canvas."""

import logging
from typing import TYPE_CHECKING

from config import MAX_CIRCLE_RADIUS, MIN_CIRCLE_RADIUS

from .base_renderer import StrokeRenderer
from .renderer_utils import stroke_color_to_rgba, validate_common_stroke_fields

if TYPE_CHECKING:
    from PIL import ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class CircleRenderer(StrokeRenderer):
    """
    Renderer for drawing circles and ellipses.

    Handles circle/ellipse drawing with support for both filled shapes and outline-only rendering.
    Uses PIL's ImageDraw.ellipse() method with RGBA color composition for transparency.
    """

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a circle stroke has all required fields and valid values.

        Args:
            stroke (Stroke): The stroke data to validate
            canvas_size (tuple[int, int]): Canvas dimensions as (width, height)

        Raises:
            ValueError: If stroke validation fails (missing fields, out of bounds, etc.)
        """
        width, height = canvas_size

        # Check required fields exist
        required_fields = [
            "center_x",
            "center_y",
            "radius",
            "fill",
            "color_hex",
            "thickness",
            "opacity",
        ]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Circle stroke missing required field: {field}")

        # Validate center coordinates
        center_x = stroke["center_x"]
        center_y = stroke["center_y"]

        if center_x is None:
            raise ValueError("Circle stroke requires center_x")
        if center_y is None:
            raise ValueError("Circle stroke requires center_y")

        # Ensure coordinates are integers
        if not isinstance(center_x, int):
            raise ValueError(f"center_x must be an integer, got {type(center_x).__name__}")
        if not isinstance(center_y, int):
            raise ValueError(f"center_y must be an integer, got {type(center_y).__name__}")

        # Check coordinates are within canvas bounds
        # Allow x == width and y == height (LLMs use canvas dimensions as the far-edge
        # coordinate; PIL clips rendering to canvas bounds automatically).
        if not (0 <= center_x <= width):
            raise ValueError(f"center_x {center_x} out of bounds [0, {width}]")
        if not (0 <= center_y <= height):
            raise ValueError(f"center_y {center_y} out of bounds [0, {height}]")

        # Validate radius
        radius = stroke["radius"]

        if radius is None:
            raise ValueError("Circle stroke requires radius")

        # Ensure radius is an integer
        if not isinstance(radius, int):
            raise ValueError(f"radius must be an integer, got {type(radius).__name__}")

        # Check radius range
        if not (MIN_CIRCLE_RADIUS <= radius <= MAX_CIRCLE_RADIUS):
            raise ValueError(
                f"radius {radius} out of range [{MIN_CIRCLE_RADIUS}, {MAX_CIRCLE_RADIUS}]"
            )

        # Check circle fits within canvas
        if center_x - radius < 0:
            raise ValueError(
                f"Circle extends beyond left edge: center_x ({center_x}) - radius ({radius}) < 0"
            )
        if center_y - radius < 0:
            raise ValueError(
                f"Circle extends beyond top edge: center_y ({center_y}) - radius ({radius}) < 0"
            )
        if center_x + radius >= width:
            raise ValueError(
                f"Circle extends beyond right edge: center_x ({center_x}) + radius ({radius}) >= {width}"
            )
        if center_y + radius >= height:
            raise ValueError(
                f"Circle extends beyond bottom edge: center_y ({center_y}) + radius ({radius}) >= {height}"
            )

        # Validate fill field
        fill = stroke["fill"]
        if fill is None:
            raise ValueError("Circle stroke requires fill field")
        if not isinstance(fill, bool):
            raise ValueError(f"fill must be a boolean, got {type(fill).__name__}")

        # Validate common stroke fields (color, thickness, opacity)
        validate_common_stroke_fields(stroke)

        logger.debug(
            f"Circle stroke validated: center=({center_x},{center_y}), radius={radius}, fill={fill}"
        )

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Render a circle stroke onto the canvas using the provided ImageDraw object.

        Args:
            stroke (Stroke): The stroke data containing circle center, radius, fill, color, and style
            draw (ImageDraw.ImageDraw): PIL ImageDraw object for drawing operations

        Raises:
            ValueError: If stroke data is invalid or incomplete
        """
        # Extract circle parameters
        center_x = stroke["center_x"]
        center_y = stroke["center_y"]
        radius = stroke["radius"]
        fill = stroke["fill"]

        if center_x is None:
            raise ValueError("Circle stroke requires center_x")
        if center_y is None:
            raise ValueError("Circle stroke requires center_y")
        if radius is None:
            raise ValueError("Circle stroke requires radius")
        if fill is None:
            raise ValueError("Circle stroke requires fill field")

        # Calculate bounding box from center and radius
        # bbox = [x0, y0, x1, y1] where (x0, y0) is top-left, (x1, y1) is bottom-right
        bbox = (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        )

        # Convert hex color to RGBA tuple with opacity
        color_rgba = stroke_color_to_rgba(stroke["color_hex"], stroke["opacity"])

        # Draw circle based on fill setting
        if fill:
            # Draw filled circle
            draw.ellipse(bbox, fill=color_rgba)
        else:
            # Draw outline circle with specified thickness
            thickness = stroke["thickness"]
            draw.ellipse(bbox, outline=color_rgba, width=thickness)

        logger.debug(
            f"Rendered {'filled' if fill else 'outline'} circle at ({center_x},{center_y}) "
            f"with radius {radius}"
        )
