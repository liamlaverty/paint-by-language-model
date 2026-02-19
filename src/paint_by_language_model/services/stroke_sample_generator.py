"""Stroke sample image generator for VLM prompt visual context."""

import logging

from config import (
    STROKE_SAMPLE_BACKGROUND,
    STROKE_SAMPLE_HEIGHT,
    STROKE_SAMPLE_WIDTH,
    STROKES_PER_SAMPLE,
)
from models.stroke import Stroke
from services.canvas_manager import CanvasManager

logger = logging.getLogger(__name__)

# Supported stroke types
SUPPORTED_STROKE_TYPES: list[str] = ["line", "arc", "polyline", "circle", "splatter"]


class StrokeSampleGenerator:
    """Generates small sample images showing example strokes for each stroke type.

    Each sample image is a 200×100 PNG containing 5 representative strokes
    rendered with varying configurations (thickness, opacity, colour, position
    and type-specific parameters). Images are generated once using the existing
    CanvasManager / renderer pipeline and cached for the lifetime of the instance.
    """

    def __init__(self) -> None:
        """Initialise the generator with an empty cache.

        The cache is populated lazily on first call to generate_sample() or
        generate_all_samples().
        """
        self._cache: dict[str, bytes] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_all_samples(self) -> dict[str, bytes]:
        """Generate sample images for all registered stroke types.

        Calls generate_sample() for each supported stroke type and collects
        the results into a single dict.  Subsequent calls return cached bytes.

        Returns:
            dict[str, bytes]: Mapping of stroke type name to PNG image bytes.
        """
        return {
            stroke_type: self.generate_sample(stroke_type) for stroke_type in SUPPORTED_STROKE_TYPES
        }

    def generate_sample(self, stroke_type: str) -> bytes:
        """Generate a single sample image for one stroke type.

        Args:
            stroke_type (str): One of "line", "arc", "polyline", "circle", "splatter".

        Returns:
            bytes: PNG-encoded image bytes (STROKE_SAMPLE_WIDTH × STROKE_SAMPLE_HEIGHT).

        Raises:
            ValueError: If stroke_type is not a recognised stroke type.
        """
        if stroke_type not in SUPPORTED_STROKE_TYPES:
            raise ValueError(
                f"Unknown stroke type: '{stroke_type}'. "
                f"Supported types are: {SUPPORTED_STROKE_TYPES}"
            )

        if stroke_type in self._cache:
            logger.debug("Returning cached sample image for stroke type '%s'", stroke_type)
            return self._cache[stroke_type]

        logger.info("Generating sample image for stroke type '%s'", stroke_type)

        strokes = self._get_sample_strokes(stroke_type)
        canvas = CanvasManager(
            width=STROKE_SAMPLE_WIDTH,
            height=STROKE_SAMPLE_HEIGHT,
            background_color=STROKE_SAMPLE_BACKGROUND,
        )
        for stroke in strokes:
            canvas.apply_stroke(stroke)

        image_bytes = canvas.get_image_bytes(format="PNG")

        self._cache[stroke_type] = image_bytes
        logger.debug(
            "Cached sample image for '%s' (%d bytes, %d strokes)",
            stroke_type,
            len(image_bytes),
            STROKES_PER_SAMPLE,
        )
        return image_bytes

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_sample_strokes(self, stroke_type: str) -> list[Stroke]:
        """Dispatch to the per-type sample stroke generator.

        Args:
            stroke_type (str): Stroke type name.

        Returns:
            list[Stroke]: A list of STROKES_PER_SAMPLE Stroke dicts.
        """
        generators = {
            "line": self._generate_line_samples,
            "arc": self._generate_arc_samples,
            "polyline": self._generate_polyline_samples,
            "circle": self._generate_circle_samples,
            "splatter": self._generate_splatter_samples,
        }
        return generators[stroke_type]()

    def _generate_line_samples(self) -> list[Stroke]:
        """Generate 5 varied line strokes for the sample canvas.

        Variations cover different angles (horizontal, vertical, diagonal,
        short), thicknesses (2–15 px), opacities (0.3–1.0), and 5 distinct
        colours spread across the 200×100 canvas.

        Returns:
            list[Stroke]: List of 5 line Stroke dicts.
        """
        return [
            # Horizontal line — red, thick, fully opaque
            Stroke(
                type="line",
                color_hex="#CC0000",
                thickness=8,
                opacity=1.0,
                start_x=10,
                start_y=20,
                end_x=190,
                end_y=20,
            ),
            # Vertical line — blue, medium, semi-transparent
            Stroke(
                type="line",
                color_hex="#0044CC",
                thickness=4,
                opacity=0.7,
                start_x=50,
                start_y=5,
                end_x=50,
                end_y=95,
            ),
            # Diagonal top-left → bottom-right — green, thin
            Stroke(
                type="line",
                color_hex="#226622",
                thickness=2,
                opacity=0.9,
                start_x=10,
                start_y=10,
                end_x=190,
                end_y=90,
            ),
            # Diagonal top-right → bottom-left — orange, thick
            Stroke(
                type="line",
                color_hex="#FF8800",
                thickness=15,
                opacity=0.5,
                start_x=190,
                start_y=10,
                end_x=100,
                end_y=90,
            ),
            # Short diagonal — purple, medium opacity
            Stroke(
                type="line",
                color_hex="#7700AA",
                thickness=6,
                opacity=0.8,
                start_x=130,
                start_y=40,
                end_x=175,
                end_y=70,
            ),
        ]

    def _generate_arc_samples(self) -> list[Stroke]:
        """Generate 5 varied arc strokes for the sample canvas.

        Variations cover different bounding-box sizes, angle sweeps (45°,
        120°, 270°, 360°), thicknesses, and 5 distinct colours.

        Returns:
            list[Stroke]: List of 5 arc Stroke dicts.
        """
        return [
            # Small arc, 45° sweep — red
            Stroke(
                type="arc",
                color_hex="#CC0000",
                thickness=3,
                opacity=1.0,
                arc_bbox=[10, 10, 60, 50],
                arc_start_angle=0,
                arc_end_angle=45,
            ),
            # Medium arc, 120° sweep — blue
            Stroke(
                type="arc",
                color_hex="#0044CC",
                thickness=5,
                opacity=0.85,
                arc_bbox=[60, 15, 130, 75],
                arc_start_angle=30,
                arc_end_angle=150,
            ),
            # Large arc, 270° sweep — green, thick
            Stroke(
                type="arc",
                color_hex="#226622",
                thickness=10,
                opacity=0.7,
                arc_bbox=[140, 5, 195, 55],
                arc_start_angle=90,
                arc_end_angle=360,
            ),
            # Full circle via arc (360°) — orange, thin
            Stroke(
                type="arc",
                color_hex="#FF8800",
                thickness=2,
                opacity=0.6,
                arc_bbox=[20, 55, 80, 95],
                arc_start_angle=0,
                arc_end_angle=360,
            ),
            # Wide flat arc — purple
            Stroke(
                type="arc",
                color_hex="#7700AA",
                thickness=7,
                opacity=0.9,
                arc_bbox=[100, 50, 190, 95],
                arc_start_angle=180,
                arc_end_angle=360,
            ),
        ]

    def _generate_polyline_samples(self) -> list[Stroke]:
        """Generate 5 varied polyline strokes for the sample canvas.

        Variations cover different point counts (3–7), path shapes (zigzag,
        wave, angular, curve-like, spiral-like), thicknesses, and 5 distinct
        colours.

        Returns:
            list[Stroke]: List of 5 polyline Stroke dicts.
        """
        return [
            # 3-point angular — red, thick
            Stroke(
                type="polyline",
                color_hex="#CC0000",
                thickness=8,
                opacity=1.0,
                points=[[10, 10], [100, 50], [190, 10]],
            ),
            # 5-point zigzag — blue
            Stroke(
                type="polyline",
                color_hex="#0044CC",
                thickness=4,
                opacity=0.8,
                points=[[10, 80], [50, 55], [90, 80], [130, 55], [170, 80]],
            ),
            # 7-point wave — green, thin
            Stroke(
                type="polyline",
                color_hex="#226622",
                thickness=2,
                opacity=0.9,
                points=[
                    [10, 50],
                    [35, 25],
                    [60, 50],
                    [85, 75],
                    [110, 50],
                    [145, 25],
                    [180, 50],
                ],
            ),
            # 4-point angular path — orange
            Stroke(
                type="polyline",
                color_hex="#FF8800",
                thickness=6,
                opacity=0.6,
                points=[[20, 20], [20, 60], [160, 60], [160, 20]],
            ),
            # 6-point spiral-like — purple
            Stroke(
                type="polyline",
                color_hex="#7700AA",
                thickness=3,
                opacity=0.75,
                points=[
                    [100, 50],
                    [130, 30],
                    [155, 55],
                    [125, 80],
                    [85, 65],
                    [90, 35],
                ],
            ),
        ]

    def _generate_circle_samples(self) -> list[Stroke]:
        """Generate 5 varied circle strokes for the sample canvas.

        Variations cover a mix of filled and outline circles, different radii
        (small, medium, large), varied positions, and 5 distinct colours.

        Returns:
            list[Stroke]: List of 5 circle Stroke dicts.
        """
        return [
            # Small filled circle — red
            Stroke(
                type="circle",
                color_hex="#CC0000",
                thickness=2,
                opacity=1.0,
                center_x=25,
                center_y=25,
                radius=12,
                fill=True,
            ),
            # Medium outline circle — blue
            Stroke(
                type="circle",
                color_hex="#0044CC",
                thickness=4,
                opacity=0.85,
                center_x=80,
                center_y=50,
                radius=30,
                fill=False,
            ),
            # Large filled circle (partially clipped ok) — green, translucent
            Stroke(
                type="circle",
                color_hex="#226622",
                thickness=3,
                opacity=0.4,
                center_x=155,
                center_y=50,
                radius=40,
                fill=True,
            ),
            # Small outline circle — orange
            Stroke(
                type="circle",
                color_hex="#FF8800",
                thickness=6,
                opacity=0.9,
                center_x=40,
                center_y=78,
                radius=15,
                fill=False,
            ),
            # Medium filled circle — purple
            Stroke(
                type="circle",
                color_hex="#7700AA",
                thickness=2,
                opacity=0.7,
                center_x=150,
                center_y=20,
                radius=18,
                fill=True,
            ),
        ]

    def _generate_splatter_samples(self) -> list[Stroke]:
        """Generate 5 varied splatter strokes for the sample canvas.

        Variations cover different splatter_radius values, splatter_count
        values, and dot_size_min/max ranges spread across the 200×100 canvas.

        Returns:
            list[Stroke]: List of 5 splatter Stroke dicts.
        """
        return [
            # Dense fine splatter — red
            Stroke(
                type="splatter",
                color_hex="#CC0000",
                thickness=1,
                opacity=1.0,
                center_x=30,
                center_y=25,
                splatter_radius=20,
                splatter_count=30,
                dot_size_min=1,
                dot_size_max=3,
            ),
            # Sparse large-dot splatter — blue
            Stroke(
                type="splatter",
                color_hex="#0044CC",
                thickness=1,
                opacity=0.8,
                center_x=100,
                center_y=50,
                splatter_radius=35,
                splatter_count=10,
                dot_size_min=4,
                dot_size_max=10,
            ),
            # Medium splatter, semi-transparent — green
            Stroke(
                type="splatter",
                color_hex="#226622",
                thickness=1,
                opacity=0.6,
                center_x=170,
                center_y=30,
                splatter_radius=25,
                splatter_count=20,
                dot_size_min=2,
                dot_size_max=6,
            ),
            # Tight tiny-dot splatter — orange
            Stroke(
                type="splatter",
                color_hex="#FF8800",
                thickness=1,
                opacity=0.9,
                center_x=50,
                center_y=75,
                splatter_radius=12,
                splatter_count=40,
                dot_size_min=1,
                dot_size_max=2,
            ),
            # Wide sparse splatter — purple
            Stroke(
                type="splatter",
                color_hex="#7700AA",
                thickness=1,
                opacity=0.75,
                center_x=145,
                center_y=75,
                splatter_radius=45,
                splatter_count=15,
                dot_size_min=3,
                dot_size_max=8,
            ),
        ]
