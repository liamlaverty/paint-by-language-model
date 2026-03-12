"""Burn renderer for darkening pixels in a circular region using multiply blend."""

import logging
from typing import TYPE_CHECKING

import numpy as np
from PIL import ImageChops

from config import (
    MAX_BURN_DODGE_INTENSITY,
    MAX_BURN_DODGE_RADIUS,
    MIN_BURN_DODGE_INTENSITY,
    MIN_BURN_DODGE_RADIUS,
)

from .base_renderer import StrokeRenderer
from .renderer_utils import validate_common_stroke_fields

if TYPE_CHECKING:
    from PIL import Image, ImageDraw

    from models import Stroke

logger = logging.getLogger(__name__)


class BurnRenderer(StrokeRenderer):
    """
    Renderer for burn strokes that darken pixels in a soft circular region.

    Uses a radial gradient multiply blend to progressively darken existing
    pixels from the centre of the specified region outwards. The centre is
    darkened most (proportional to ``intensity``), falling off linearly to no
    effect at the edge of the radius.  Effective for shadow modelling, depth,
    and vignetting effects.

    This renderer requires direct PIL Image access and uses the
    ``render_to_image()`` path instead of ``render()``.
    """

    @property
    def needs_image_access(self) -> bool:
        """Whether this renderer needs direct PIL Image access.

        Returns:
            bool: Always ``True`` — burn uses ``render_to_image()`` for
                multiply-blend compositing.
        """
        return True

    def validate(self, stroke: "Stroke", canvas_size: tuple[int, int]) -> None:
        """
        Validate that a burn stroke has all required fields and valid values.

        Args:
            stroke (Stroke): The stroke data to validate.
            canvas_size (tuple[int, int]): Canvas dimensions as (width, height).

        Raises:
            ValueError: If stroke validation fails — missing fields, out-of-bounds
                coordinates, out-of-range ``radius`` or ``intensity``, or incorrect
                field types.
        """
        width, height = canvas_size

        # Check required fields exist
        required_fields = [
            "center_x",
            "center_y",
            "radius",
            "intensity",
            "color_hex",
            "thickness",
            "opacity",
        ]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Burn stroke missing required field: {field}")

        # Validate center_x
        center_x = stroke["center_x"]
        if not isinstance(center_x, int):
            raise ValueError(f"center_x must be an integer, got {type(center_x).__name__}")
        if not (0 <= center_x <= width):
            raise ValueError(f"center_x {center_x} out of bounds [0, {width}]")

        # Validate center_y
        center_y = stroke["center_y"]
        if not isinstance(center_y, int):
            raise ValueError(f"center_y must be an integer, got {type(center_y).__name__}")
        if not (0 <= center_y <= height):
            raise ValueError(f"center_y {center_y} out of bounds [0, {height}]")

        # Validate radius
        radius = stroke["radius"]
        if not isinstance(radius, int):
            raise ValueError(f"radius must be an integer, got {type(radius).__name__}")
        if not (MIN_BURN_DODGE_RADIUS <= radius <= MAX_BURN_DODGE_RADIUS):
            raise ValueError(
                f"radius {radius} out of range [{MIN_BURN_DODGE_RADIUS}, {MAX_BURN_DODGE_RADIUS}]"
            )

        # Validate intensity
        intensity = stroke["intensity"]
        if not isinstance(intensity, (int, float)):
            raise ValueError(f"intensity must be a number, got {type(intensity).__name__}")
        if not (MIN_BURN_DODGE_INTENSITY <= intensity <= MAX_BURN_DODGE_INTENSITY):
            raise ValueError(
                f"intensity {intensity} out of range "
                f"[{MIN_BURN_DODGE_INTENSITY}, {MAX_BURN_DODGE_INTENSITY}]"
            )

        # Validate common fields (color_hex, thickness, opacity)
        validate_common_stroke_fields(stroke)

    def render_to_image(self, stroke: "Stroke", image: "Image.Image") -> "Image.Image":
        """
        Render a burn stroke by darkening pixels in a circular region.

        Creates a greyscale radial-gradient mask centred on
        (``center_x``, ``center_y``).  The centre of the region is darkened
        most (proportional to ``intensity``), falling off linearly to no effect
        at the edge of the radius.  The mask is applied via
        ``ImageChops.multiply`` so that unaffected pixels remain unchanged.

        Uses NumPy for vectorised per-pixel factor computation.

        Args:
            stroke (Stroke): Stroke data including ``center_x``, ``center_y``,
                ``radius``, and ``intensity``.
            image (Image.Image): The current canvas PIL Image in ``RGB`` mode.

        Returns:
            Image.Image: The modified canvas image with the burn effect applied.
        """
        from PIL import Image as PILImage

        raw_cx = stroke["center_x"]
        raw_cy = stroke["center_y"]
        raw_radius = stroke["radius"]
        raw_intensity = stroke["intensity"]

        if raw_cx is None:
            raise ValueError("center_x is required for burn strokes")
        if raw_cy is None:
            raise ValueError("center_y is required for burn strokes")
        if raw_radius is None:
            raise ValueError("radius is required for burn strokes")
        if raw_intensity is None:
            raise ValueError("intensity is required for burn strokes")

        cx = int(raw_cx)
        cy = int(raw_cy)
        radius = int(raw_radius)
        intensity = float(raw_intensity)

        img_width, img_height = image.size

        # Compute bounding box of the affected region, clamped to canvas bounds
        x_min = max(0, cx - radius)
        x_max = min(img_width - 1, cx + radius)
        y_min = max(0, cy - radius)
        y_max = min(img_height - 1, cy + radius)

        if x_min > x_max or y_min > y_max:
            # Burn region entirely outside canvas — no change
            return image

        # Build a white mask image (white = no effect under multiply)
        mask_array = np.full((img_height, img_width, 3), 255, dtype=np.float32)

        # Vectorised distance computation over the bounding box
        xs = np.arange(x_min, x_max + 1, dtype=np.float32)
        ys = np.arange(y_min, y_max + 1, dtype=np.float32)
        grid_x, grid_y = np.meshgrid(xs, ys)
        dist = np.sqrt((grid_x - cx) ** 2 + (grid_y - cy) ** 2)

        # Pixels within the radius get darkened proportional to intensity
        within = dist < radius
        factor = np.where(within, intensity * (1.0 - dist / radius), 0.0)
        factor = np.clip(factor, 0.0, 1.0)

        # v = 255 * (1 - factor):
        #   factor=0  → v=255 (white, no darkening)
        #   factor=1  → v=0   (black, full darkening)
        v = (255.0 * (1.0 - factor)).astype(np.float32)

        # Write the greyscale values into the bounding box region of the mask
        mask_array[y_min : y_max + 1, x_min : x_max + 1, 0] = v
        mask_array[y_min : y_max + 1, x_min : x_max + 1, 1] = v
        mask_array[y_min : y_max + 1, x_min : x_max + 1, 2] = v

        mask = PILImage.fromarray(mask_array.astype(np.uint8), "RGB")
        result = ImageChops.multiply(image, mask)
        return result

    def render(self, stroke: "Stroke", draw: "ImageDraw.ImageDraw") -> None:
        """
        Not supported for burn strokes — always raises ``RuntimeError``.

        Burn strokes must use ``render_to_image()`` because they need direct
        pixel-level access to the underlying PIL Image.

        Args:
            stroke (Stroke): Unused.
            draw (ImageDraw.ImageDraw): Unused.

        Raises:
            RuntimeError: Always — burn strokes must use ``render_to_image()``.
        """
        raise RuntimeError("Use render_to_image() for burn strokes")
