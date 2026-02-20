"""Arc renderer for drawing elliptical arcs on canvas."""

import logging
from typing import TYPE_CHECKING

from config import MAX_ARC_ANGLE

from .base_renderer import StrokeRenderer
from .renderer_utils import stroke_color_to_rgba, validate_common_stroke_fields

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
        # Allow x == width and y == height (LLMs use canvas dimensions as the far-edge
        # coordinate; PIL clips rendering to canvas bounds automatically).
        if not (0 <= x0 <= width):
            raise ValueError(f"arc_bbox x0 {x0} out of bounds [0, {width}]")
        if not (0 <= y0 <= height):
            raise ValueError(f"arc_bbox y0 {y0} out of bounds [0, {height}]")
        if not (0 <= x1 <= width):
            raise ValueError(f"arc_bbox x1 {x1} out of bounds [0, {width}]")
        if not (0 <= y1 <= height):
            raise ValueError(f"arc_bbox y1 {y1} out of bounds [0, {height}]")

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

        # Validate common stroke fields (color, thickness, opacity)
        validate_common_stroke_fields(stroke)

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

        # Convert hex color to RGBA tuple with opacity
        color_rgba = stroke_color_to_rgba(stroke["color_hex"], stroke["opacity"])

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
            f"color={stroke['color_hex']}, thickness={thickness}, opacity={stroke['opacity']}"
        )
