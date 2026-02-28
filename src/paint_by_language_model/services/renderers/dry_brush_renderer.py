"""Dry-brush renderer for creating textured brush strokes with gaps."""

import logging
import math
from typing import TYPE_CHECKING

from config import (
    MAX_BRISTLE_COUNT,
    MAX_BRUSH_WIDTH,
    MAX_GAP_PROBABILITY,
    MAX_POLYLINE_POINTS,
    MIN_BRISTLE_COUNT,
    MIN_BRUSH_WIDTH,
    MIN_GAP_PROBABILITY,
    MIN_POLYLINE_POINTS,
)

from .base_renderer import StrokeRenderer
from .prng import mulberry32
from .renderer_utils import stroke_color_to_rgba, validate_common_stroke_fields

if TYPE_CHECKING:
    from PIL import ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class DryBrushRenderer(StrokeRenderer):
    """
    Renderer for dry-brush strokes with visible bristle gaps.

    Creates textured brush strokes by drawing multiple parallel bristle lines
    with seeded-random gaps and jitter. Each bristle follows the polyline path
    with slight perpendicular offset and random segment skipping based on
    gap_probability. Uses deterministic PRNG for reproducible rendering.
    """

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a dry-brush stroke has all required fields and valid values.

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
            "brush_width",
            "bristle_count",
            "gap_probability",
            "color_hex",
            "thickness",
            "opacity",
        ]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Dry-brush stroke missing required field: {field}")

        # Validate points (same as polyline)
        points = stroke["points"]

        if not isinstance(points, list):
            raise ValueError(f"points must be a list, got {type(points).__name__}")

        if len(points) < MIN_POLYLINE_POINTS:
            raise ValueError(
                f"Dry-brush must have at least {MIN_POLYLINE_POINTS} points, got {len(points)}"
            )

        if len(points) > MAX_POLYLINE_POINTS:
            raise ValueError(
                f"Dry-brush cannot have more than {MAX_POLYLINE_POINTS} points, got {len(points)}"
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

        # Validate brush_width
        brush_width = stroke["brush_width"]

        if brush_width is None:
            raise ValueError("Dry-brush stroke requires brush_width")

        if not isinstance(brush_width, int):
            raise ValueError(f"brush_width must be an integer, got {type(brush_width).__name__}")

        if not (MIN_BRUSH_WIDTH <= brush_width <= MAX_BRUSH_WIDTH):
            raise ValueError(
                f"brush_width {brush_width} out of range [{MIN_BRUSH_WIDTH}, {MAX_BRUSH_WIDTH}]"
            )

        # Validate bristle_count
        bristle_count = stroke["bristle_count"]

        if bristle_count is None:
            raise ValueError("Dry-brush stroke requires bristle_count")

        if not isinstance(bristle_count, int):
            raise ValueError(
                f"bristle_count must be an integer, got {type(bristle_count).__name__}"
            )

        if not (MIN_BRISTLE_COUNT <= bristle_count <= MAX_BRISTLE_COUNT):
            raise ValueError(
                f"bristle_count {bristle_count} out of range [{MIN_BRISTLE_COUNT}, {MAX_BRISTLE_COUNT}]"
            )

        # Validate gap_probability
        gap_probability = stroke["gap_probability"]

        if gap_probability is None:
            raise ValueError("Dry-brush stroke requires gap_probability")

        if not isinstance(gap_probability, (int, float)):
            raise ValueError(
                f"gap_probability must be a number, got {type(gap_probability).__name__}"
            )

        if not (MIN_GAP_PROBABILITY <= gap_probability <= MAX_GAP_PROBABILITY):
            raise ValueError(
                f"gap_probability {gap_probability} out of range [{MIN_GAP_PROBABILITY}, {MAX_GAP_PROBABILITY}]"
            )

        # Validate common stroke fields (color, thickness, opacity)
        validate_common_stroke_fields(stroke)

        logger.debug(
            f"Dry-brush stroke validated: {len(points)} points, "
            f"{brush_width}px wide, {bristle_count} bristles, "
            f"{gap_probability} gap probability"
        )

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Render a dry-brush stroke onto the canvas using the provided ImageDraw object.

        Creates textured brush effect by drawing multiple parallel bristle lines with
        random gaps and jitter. Each bristle follows the polyline path with perpendicular
        offset and uses PRNG to skip segments based on gap_probability.

        Args:
            stroke (Stroke): The stroke data containing dry-brush parameters
            draw (ImageDraw.ImageDraw): PIL ImageDraw object for drawing operations

        Raises:
            ValueError: If stroke data is invalid or incomplete
        """
        points = stroke.get("points")
        if points is None or len(points) < 2:
            raise ValueError("Dry-brush stroke requires at least 2 points")

        brush_width = stroke.get("brush_width")
        bristle_count = stroke.get("bristle_count")
        gap_probability = stroke.get("gap_probability")

        if brush_width is None:
            raise ValueError("Dry-brush stroke requires brush_width")
        if bristle_count is None:
            raise ValueError("Dry-brush stroke requires bristle_count")
        if gap_probability is None:
            raise ValueError("Dry-brush stroke requires gap_probability")

        # Convert hex color to RGBA tuple with opacity
        color_rgba = stroke_color_to_rgba(stroke["color_hex"], stroke["opacity"])

        # Calculate bristle thickness (distribute total thickness across bristles)
        bristle_thickness = max(1, stroke["thickness"] // bristle_count)

        # Create seed from first point coordinates for deterministic randomness
        seed = hash(tuple(points[0]))

        # Render each bristle
        for bristle_idx in range(bristle_count):
            # Create PRNG for this bristle
            rng = mulberry32(seed + bristle_idx)

            # Calculate offset for this bristle (evenly spaced across brush_width)
            # Center the bristles around the path
            if bristle_count == 1:
                offset = 0.0
            else:
                offset = (bristle_idx / (bristle_count - 1) - 0.5) * brush_width

            # Walk the polyline path segment by segment
            for seg_idx in range(len(points) - 1):
                p0 = points[seg_idx]
                p1 = points[seg_idx + 1]

                # Compute segment direction and perpendicular
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

                # Add small random jitter to perpendicular offset (±10% of brush_width)
                jitter = (rng() - 0.5) * brush_width * 0.2
                actual_offset = offset + jitter

                # Calculate bristle segment endpoints
                bristle_p0_x = p0[0] + perp_x * actual_offset
                bristle_p0_y = p0[1] + perp_y * actual_offset
                bristle_p1_x = p1[0] + perp_x * actual_offset
                bristle_p1_y = p1[1] + perp_y * actual_offset

                # Decide whether to skip this segment (create gap)
                if rng() < gap_probability:
                    continue  # Skip this segment

                # Draw this bristle segment
                draw.line(
                    [
                        (int(bristle_p0_x), int(bristle_p0_y)),
                        (int(bristle_p1_x), int(bristle_p1_y)),
                    ],
                    fill=color_rgba,
                    width=bristle_thickness,
                )

        logger.debug(
            f"Rendered dry-brush: {len(points)} points, "
            f"{bristle_count} bristles, gap_probability={gap_probability}, "
            f"color={stroke['color_hex']}, opacity={stroke['opacity']}"
        )
