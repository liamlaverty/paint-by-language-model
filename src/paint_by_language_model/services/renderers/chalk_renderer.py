"""Chalk renderer for creating grainy, textured chalk strokes on canvas."""

import logging
import math
from typing import TYPE_CHECKING

from config import (
    MAX_CHALK_WIDTH,
    MAX_GRAIN_DENSITY,
    MAX_POLYLINE_POINTS,
    MIN_CHALK_WIDTH,
    MIN_GRAIN_DENSITY,
    MIN_POLYLINE_POINTS,
)

from .base_renderer import StrokeRenderer
from .prng import mulberry32
from .renderer_utils import stroke_color_to_rgba, validate_common_stroke_fields

if TYPE_CHECKING:
    from PIL import ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class ChalkRenderer(StrokeRenderer):
    """
    Renderer for chalk strokes with grainy texture.

    Creates grainy, textured strokes along a polyline path by generating many
    small random dots clustered within a perpendicular band. Mimics chalk or
    pastel on rough paper. Uses deterministic PRNG for reproducible rendering.
    """

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a chalk stroke has all required fields and valid values.

        Args:
            stroke (Stroke): The stroke data to validate
            canvas_size (tuple[int, int]): Canvas dimensions as (width, height)

        Raises:
            ValueError: If stroke validation fails (missing fields, out of bounds, etc.)
        """
        width, height = canvas_size

        # Check required fields exist
        required_fields = [
            "points",
            "chalk_width",
            "grain_density",
            "color_hex",
            "thickness",
            "opacity",
        ]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Chalk stroke missing required field: {field}")

        # Validate points (same as polyline)
        points = stroke["points"]

        if not isinstance(points, list):
            raise ValueError(f"points must be a list, got {type(points).__name__}")

        if len(points) < MIN_POLYLINE_POINTS:
            raise ValueError(
                f"Chalk must have at least {MIN_POLYLINE_POINTS} points, got {len(points)}"
            )

        if len(points) > MAX_POLYLINE_POINTS:
            raise ValueError(
                f"Chalk cannot have more than {MAX_POLYLINE_POINTS} points, got {len(points)}"
            )

        # Validate each point
        for i, point in enumerate(points):
            if not isinstance(point, (list, tuple)):
                raise ValueError(f"Point {i} must be a list or tuple, got {type(point).__name__}")

            if len(point) != 2:
                raise ValueError(f"Point {i} must have exactly 2 coordinates, got {len(point)}")

            x, y = point

            if not isinstance(x, int):
                raise ValueError(
                    f"Point {i} x-coordinate must be an integer, got {type(x).__name__}"
                )
            if not isinstance(y, int):
                raise ValueError(
                    f"Point {i} y-coordinate must be an integer, got {type(y).__name__}"
                )

            if not (0 <= x <= width):
                raise ValueError(f"Point {i} x-coordinate {x} out of bounds [0, {width}]")
            if not (0 <= y <= height):
                raise ValueError(f"Point {i} y-coordinate {y} out of bounds [0, {height}]")

        # Validate chalk_width
        chalk_width = stroke["chalk_width"]

        if chalk_width is None:
            raise ValueError("Chalk stroke requires chalk_width")

        if not isinstance(chalk_width, int):
            raise ValueError(f"chalk_width must be an integer, got {type(chalk_width).__name__}")

        if not (MIN_CHALK_WIDTH <= chalk_width <= MAX_CHALK_WIDTH):
            raise ValueError(
                f"chalk_width {chalk_width} out of range [{MIN_CHALK_WIDTH}, {MAX_CHALK_WIDTH}]"
            )

        # Validate grain_density
        grain_density = stroke["grain_density"]

        if grain_density is None:
            raise ValueError("Chalk stroke requires grain_density")

        if not isinstance(grain_density, int):
            raise ValueError(
                f"grain_density must be an integer, got {type(grain_density).__name__}"
            )

        if not (MIN_GRAIN_DENSITY <= grain_density <= MAX_GRAIN_DENSITY):
            raise ValueError(
                f"grain_density {grain_density} out of range [{MIN_GRAIN_DENSITY}, {MAX_GRAIN_DENSITY}]"
            )

        # Validate common stroke fields (color, thickness, opacity)
        validate_common_stroke_fields(stroke)

        logger.debug(
            f"Chalk stroke validated: {len(points)} points, "
            f"{chalk_width}px wide, grain_density={grain_density}"
        )

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Render a chalk stroke onto the canvas using the provided ImageDraw object.

        Creates grainy textured effect by walking the polyline path and generating
        random dots within a perpendicular band at each sample point. Uses PRNG for
        deterministic dot placement.

        Args:
            stroke (Stroke): The stroke data containing chalk parameters
            draw (ImageDraw.ImageDraw): PIL ImageDraw object for drawing operations

        Raises:
            ValueError: If stroke data is invalid or incomplete
        """
        points = stroke.get("points")
        if points is None or len(points) < 2:
            raise ValueError("Chalk stroke requires at least 2 points")

        chalk_width = stroke.get("chalk_width")
        grain_density = stroke.get("grain_density")

        if chalk_width is None:
            raise ValueError("Chalk stroke requires chalk_width")
        if grain_density is None:
            raise ValueError("Chalk stroke requires grain_density")

        # Convert hex color to RGBA tuple with opacity
        color_rgba = stroke_color_to_rgba(stroke["color_hex"], stroke["opacity"])

        # Get canvas dimensions
        canvas_width, canvas_height = draw.im.size

        # Walk the polyline path and generate sample points
        sample_spacing = 2.0  # pixels between sample points

        for seg_idx in range(len(points) - 1):
            p0 = points[seg_idx]
            p1 = points[seg_idx + 1]

            # Compute segment direction and length
            dx = p1[0] - p0[0]
            dy = p1[1] - p0[1]
            length = math.sqrt(dx * dx + dy * dy)

            if length < 0.001:  # Skip degenerate segments
                continue

            # Normalize direction vector
            dir_x = dx / length
            dir_y = dy / length

            # Perpendicular direction (rotated 90 degrees)
            perp_x = -dir_y
            perp_y = dir_x

            # Generate evenly-spaced sample points along this segment
            num_samples = max(1, int(length / sample_spacing))

            for sample_idx in range(num_samples):
                # Calculate position along segment
                t = sample_idx / max(1, num_samples - 1) if num_samples > 1 else 0.5
                sample_x = p0[0] + t * dx
                sample_y = p0[1] + t * dy

                # Create seed from sample point coordinates for deterministic randomness
                seed = hash((seg_idx, sample_idx, int(sample_x), int(sample_y)))

                # Generate grain_density random dots at this sample point
                rng = mulberry32(seed)

                for _dot_idx in range(grain_density):
                    # Random perpendicular offset within ±chalk_width/2
                    perp_offset = (rng() - 0.5) * chalk_width

                    # Random radius between 1 and 3 pixels
                    dot_radius = 1 + rng() * 2

                    # Calculate dot position
                    dot_x = sample_x + perp_x * perp_offset
                    dot_y = sample_y + perp_y * perp_offset

                    # Skip dots that fall entirely outside canvas bounds
                    if (
                        dot_x + dot_radius < 0
                        or dot_y + dot_radius < 0
                        or dot_x - dot_radius >= canvas_width
                        or dot_y - dot_radius >= canvas_height
                    ):
                        continue

                    # Draw dot as small ellipse
                    bbox = (
                        int(dot_x - dot_radius),
                        int(dot_y - dot_radius),
                        int(dot_x + dot_radius),
                        int(dot_y + dot_radius),
                    )
                    draw.ellipse(bbox, fill=color_rgba)

        logger.debug(
            f"Rendered chalk: {len(points)} points, "
            f"chalk_width={chalk_width}px, grain_density={grain_density}, "
            f"color={stroke['color_hex']}, opacity={stroke['opacity']}"
        )
