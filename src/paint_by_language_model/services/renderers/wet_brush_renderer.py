"""Wet-brush renderer for creating soft-edged, bleeding strokes."""

import logging
from typing import TYPE_CHECKING

from config import (
    MAX_FLOW,
    MAX_POLYLINE_POINTS,
    MAX_SOFTNESS,
    MIN_FLOW,
    MIN_POLYLINE_POINTS,
    MIN_SOFTNESS,
)

from .base_renderer import StrokeRenderer
from .renderer_utils import hex_to_rgb, validate_common_stroke_fields

if TYPE_CHECKING:
    from PIL import Image, ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class WetBrushRenderer(StrokeRenderer):
    """
    Renderer for wet-brush strokes with soft, bleeding edges.

    Creates a watercolour-like effect by drawing a polyline onto a temporary
    transparent RGBA layer, applying a Gaussian blur to simulate paint bleed,
    and alpha-compositing the result onto the main canvas. This renderer
    requires direct PIL Image access and uses the render_to_image() path.
    """

    @property
    def needs_image_access(self) -> bool:
        """Whether this renderer needs direct PIL Image access.

        Returns:
            bool: Always True — wet-brush uses render_to_image() for blur
                compositing.
        """
        return True

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a wet-brush stroke has all required fields and valid values.

        Args:
            stroke (Stroke): The stroke data to validate
            canvas_size (tuple[int, int]): Canvas dimensions as (width, height)

        Raises:
            ValueError: If stroke validation fails (missing fields, out of bounds,
                invalid types, or values outside allowed ranges)
        """
        width, height = canvas_size

        # Check required fields exist
        required_fields = [
            "points",
            "softness",
            "flow",
            "color_hex",
            "thickness",
            "opacity",
        ]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Wet-brush stroke missing required field: {field}")

        # Validate points
        points = stroke["points"]

        if not isinstance(points, list):
            raise ValueError(f"points must be a list, got {type(points).__name__}")

        if len(points) < MIN_POLYLINE_POINTS:
            raise ValueError(
                f"Wet-brush must have at least {MIN_POLYLINE_POINTS} points, got {len(points)}"
            )

        if len(points) > MAX_POLYLINE_POINTS:
            raise ValueError(
                f"Wet-brush cannot have more than {MAX_POLYLINE_POINTS} points, got {len(points)}"
            )

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

        # Validate softness
        softness = stroke["softness"]

        if not isinstance(softness, int):
            raise ValueError(f"softness must be an integer, got {type(softness).__name__}")

        if not (MIN_SOFTNESS <= softness <= MAX_SOFTNESS):
            raise ValueError(f"softness {softness} out of range [{MIN_SOFTNESS}, {MAX_SOFTNESS}]")

        # Validate flow
        flow = stroke["flow"]

        if not isinstance(flow, (int, float)):
            raise ValueError(f"flow must be a number, got {type(flow).__name__}")

        if not (MIN_FLOW <= flow <= MAX_FLOW):
            raise ValueError(f"flow {flow} out of range [{MIN_FLOW}, {MAX_FLOW}]")

        # Validate common stroke fields (color, thickness, opacity)
        validate_common_stroke_fields(stroke)

        logger.debug(
            f"Wet-brush stroke validated: {len(points)} points, softness={softness}, flow={flow}"
        )

    def render_to_image(self, stroke: "Stroke", image: "Image.Image") -> "Image.Image":
        """
        Render a wet-brush stroke onto the canvas image with Gaussian blur bleed.

        Algorithm:
            1. Create a temporary transparent RGBA layer the same size as the canvas.
            2. Draw the polyline onto the temp layer using the stroke colour with
               an effective alpha computed from `opacity * flow`.
            3. Apply a Gaussian blur (radius = softness) to the temp layer to
               simulate paint bleeding at the edges.
            4. Alpha-composite the blurred layer onto the main canvas and return
               the result as an RGB image.

        Args:
            stroke (Stroke): The stroke data containing wet-brush parameters
            image (Image.Image): The current canvas PIL Image (RGB mode)

        Returns:
            Image.Image: The modified canvas image in RGB mode
        """
        from PIL import Image, ImageDraw, ImageFilter

        points = stroke["points"]
        softness = stroke["softness"]
        raw_flow = stroke["flow"]

        if points is None:
            raise ValueError("points is required for wet-brush strokes")
        if softness is None:
            raise ValueError("softness is required for wet-brush strokes")
        if raw_flow is None:
            raise ValueError("flow is required for wet-brush strokes")

        flow = float(raw_flow)
        opacity = float(stroke["opacity"])
        thickness = int(stroke["thickness"])
        color_hex = stroke["color_hex"]

        # Convert hex to RGB components
        r, g, b = hex_to_rgb(color_hex)

        # Compute effective alpha clamped to [0, 255]
        alpha = int(opacity * flow * 255)
        alpha = max(0, min(255, alpha))

        color_rgba = (r, g, b, alpha)

        # Convert points to list of tuples for PIL
        points_tuples = [(int(p[0]), int(p[1])) for p in points]

        # Create temporary RGBA layer
        temp = Image.new("RGBA", image.size, (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp, "RGBA")

        # Draw polyline onto temp layer
        temp_draw.line(points_tuples, fill=color_rgba, width=thickness)

        # Apply Gaussian blur to simulate paint bleed
        temp = temp.filter(ImageFilter.GaussianBlur(radius=softness))

        # Alpha-composite onto main canvas and convert back to RGB
        result = Image.alpha_composite(image.convert("RGBA"), temp).convert("RGB")

        logger.debug(
            f"Wet-brush rendered: {len(points)} points, "
            f"softness={softness}, flow={flow}, alpha={alpha}"
        )

        return result

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Guard method — wet-brush strokes must use render_to_image() instead.

        This method should never be called because needs_image_access is True,
        which causes CanvasManager to route wet-brush strokes to render_to_image().
        It is implemented only to provide a clear error message if called directly.

        Args:
            stroke (Stroke): The stroke data (unused)
            draw (ImageDraw.ImageDraw): PIL ImageDraw object (unused)

        Raises:
            RuntimeError: Always, to signal incorrect dispatch.
        """
        raise RuntimeError("Use render_to_image() for wet-brush strokes")
