"""Splatter renderer for drawing random dot distributions on canvas."""

import logging
import math
import random
from typing import TYPE_CHECKING

from config import (
    MAX_DOT_SIZE,
    MAX_SPLATTER_COUNT,
    MAX_SPLATTER_RADIUS,
    MIN_DOT_SIZE,
    MIN_SPLATTER_COUNT,
    MIN_SPLATTER_RADIUS,
)

from .base_renderer import StrokeRenderer
from .renderer_utils import stroke_color_to_rgba, validate_common_stroke_fields

if TYPE_CHECKING:
    from PIL import ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class SplatterRenderer(StrokeRenderer):
    """
    Renderer for drawing random dot distributions (splatter effects).

    Handles splatter drawing by placing multiple small dots randomly distributed within a
    circular area. Each dot has random position within the splatter radius and random size
    within min/max bounds. Uses PIL's ImageDraw.ellipse() for drawing dots with RGBA color
    composition for transparency.
    """

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a splatter stroke has all required fields and valid values.

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
            "splatter_radius",
            "splatter_count",
            "dot_size_min",
            "dot_size_max",
            "color_hex",
            "opacity",
        ]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Splatter stroke missing required field: {field}")

        # Validate center coordinates
        center_x = stroke["center_x"]
        center_y = stroke["center_y"]

        if center_x is None:
            raise ValueError("Splatter stroke requires center_x")
        if center_y is None:
            raise ValueError("Splatter stroke requires center_y")

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

        # Validate splatter_radius
        splatter_radius = stroke["splatter_radius"]

        if splatter_radius is None:
            raise ValueError("Splatter stroke requires splatter_radius")

        # Ensure splatter_radius is an integer
        if not isinstance(splatter_radius, int):
            raise ValueError(
                f"splatter_radius must be an integer, got {type(splatter_radius).__name__}"
            )

        # Check splatter_radius range
        if not (MIN_SPLATTER_RADIUS <= splatter_radius <= MAX_SPLATTER_RADIUS):
            raise ValueError(
                f"splatter_radius {splatter_radius} out of range "
                f"[{MIN_SPLATTER_RADIUS}, {MAX_SPLATTER_RADIUS}]"
            )

        # Validate splatter_count
        splatter_count = stroke["splatter_count"]

        if splatter_count is None:
            raise ValueError("Splatter stroke requires splatter_count")

        # Ensure splatter_count is an integer
        if not isinstance(splatter_count, int):
            raise ValueError(
                f"splatter_count must be an integer, got {type(splatter_count).__name__}"
            )

        # Check splatter_count range
        if not (MIN_SPLATTER_COUNT <= splatter_count <= MAX_SPLATTER_COUNT):
            raise ValueError(
                f"splatter_count {splatter_count} out of range "
                f"[{MIN_SPLATTER_COUNT}, {MAX_SPLATTER_COUNT}]"
            )

        # Validate dot sizes
        dot_size_min = stroke["dot_size_min"]
        dot_size_max = stroke["dot_size_max"]

        if dot_size_min is None:
            raise ValueError("Splatter stroke requires dot_size_min")
        if dot_size_max is None:
            raise ValueError("Splatter stroke requires dot_size_max")

        # Ensure dot sizes are integers
        if not isinstance(dot_size_min, int):
            raise ValueError(f"dot_size_min must be an integer, got {type(dot_size_min).__name__}")
        if not isinstance(dot_size_max, int):
            raise ValueError(f"dot_size_max must be an integer, got {type(dot_size_max).__name__}")

        # Check dot size range
        if not (MIN_DOT_SIZE <= dot_size_min <= MAX_DOT_SIZE):
            raise ValueError(
                f"dot_size_min {dot_size_min} out of range [{MIN_DOT_SIZE}, {MAX_DOT_SIZE}]"
            )
        if not (MIN_DOT_SIZE <= dot_size_max <= MAX_DOT_SIZE):
            raise ValueError(
                f"dot_size_max {dot_size_max} out of range [{MIN_DOT_SIZE}, {MAX_DOT_SIZE}]"
            )

        # Ensure dot_size_min <= dot_size_max
        if dot_size_min > dot_size_max:
            raise ValueError(
                f"dot_size_min ({dot_size_min}) must be <= dot_size_max ({dot_size_max})"
            )

        # Validate common stroke fields (color, opacity)
        # Note: thickness is not used for splatter, but we validate it anyway if present
        if "thickness" in stroke:
            from .renderer_utils import validate_thickness

            validate_thickness(stroke["thickness"])

        validate_common_stroke_fields(stroke)

        logger.debug(
            f"Splatter stroke validated: center=({center_x},{center_y}), "
            f"radius={splatter_radius}, count={splatter_count}, "
            f"dot_size=[{dot_size_min},{dot_size_max}]"
        )

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Render a splatter stroke onto the canvas using the provided ImageDraw object.

        Generates random dot positions within the splatter radius using uniform distribution.
        Each dot is drawn as a filled circle with random size between dot_size_min and dot_size_max.
        Dots that would be entirely outside canvas bounds are skipped.

        Args:
            stroke (Stroke): The stroke data containing splatter center, radius, count, and dot sizes
            draw (ImageDraw.ImageDraw): PIL ImageDraw object for drawing operations

        Raises:
            ValueError: If stroke data is invalid or incomplete
        """
        # Extract splatter parameters
        center_x = stroke["center_x"]
        center_y = stroke["center_y"]
        splatter_radius = stroke["splatter_radius"]
        splatter_count = stroke["splatter_count"]
        dot_size_min = stroke["dot_size_min"]
        dot_size_max = stroke["dot_size_max"]

        if center_x is None:
            raise ValueError("Splatter stroke requires center_x")
        if center_y is None:
            raise ValueError("Splatter stroke requires center_y")
        if splatter_radius is None:
            raise ValueError("Splatter stroke requires splatter_radius")
        if splatter_count is None:
            raise ValueError("Splatter stroke requires splatter_count")
        if dot_size_min is None:
            raise ValueError("Splatter stroke requires dot_size_min")
        if dot_size_max is None:
            raise ValueError("Splatter stroke requires dot_size_max")

        # Get canvas dimensions from the underlying image
        canvas = draw.im
        canvas_width, canvas_height = canvas.size

        # Convert hex color and opacity to RGBA
        color_rgba = stroke_color_to_rgba(stroke["color_hex"], stroke["opacity"])

        # Generate and draw random dots
        dots_drawn = 0
        dots_skipped = 0

        for _ in range(splatter_count):
            # Generate random position using uniform distribution within circle
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, splatter_radius)

            dot_x = int(center_x + distance * math.cos(angle))
            dot_y = int(center_y + distance * math.sin(angle))

            # Generate random dot size
            dot_radius = random.randint(dot_size_min, dot_size_max)

            # Calculate dot bounding box
            dot_bbox = [
                dot_x - dot_radius,
                dot_y - dot_radius,
                dot_x + dot_radius,
                dot_y + dot_radius,
            ]

            # Skip dots that would be entirely outside canvas bounds
            # (PIL will clip partial overlaps automatically)
            if (
                dot_bbox[2] < 0
                or dot_bbox[3] < 0
                or dot_bbox[0] >= canvas_width
                or dot_bbox[1] >= canvas_height
            ):
                dots_skipped += 1
                continue

            # Draw the dot as a filled circle
            draw.ellipse(dot_bbox, fill=color_rgba)
            dots_drawn += 1

        logger.debug(
            f"Splatter stroke rendered: {dots_drawn} dots drawn, {dots_skipped} dots skipped"
        )
