"""Stroke sample image generator for VLM prompt visual context."""

import logging
from pathlib import Path

from config import (
    MAX_BURN_DODGE_INTENSITY,
    MAX_BURN_DODGE_RADIUS,
    MAX_FLOW,
    MAX_SOFTNESS,
    MIN_BURN_DODGE_INTENSITY,
    MIN_BURN_DODGE_RADIUS,
    MIN_FLOW,
    MIN_SOFTNESS,
    STROKE_SAMPLE_BACKGROUND,
    STROKE_SAMPLE_DIR,
    STROKE_SAMPLE_HEIGHT,
    STROKE_SAMPLE_WIDTH,
    STROKES_PER_SAMPLE,
)
from models.stroke import Stroke
from services.canvas_manager import CanvasManager

logger = logging.getLogger(__name__)

# Supported stroke types
SUPPORTED_STROKE_TYPES: list[str] = [
    "line",
    "arc",
    "polyline",
    "circle",
    "splatter",
    "dry-brush",
    "chalk",
    "wet-brush",
    "burn",
    "dodge",
]


class StrokeSampleGenerator:
    """Generates small sample images showing example strokes for each stroke type.

    Each sample image is a 200×100 PNG containing 5 representative strokes
    rendered with varying configurations (thickness, opacity, colour, position
    and type-specific parameters). Images are generated once using the existing
    CanvasManager / renderer pipeline, persisted to disk under ``output_dir``,
    and cached in-memory for the lifetime of the instance.

    Persisting samples to disk makes it possible to inspect exactly what visual
    context was provided to the VLM during a generation run.
    """

    def __init__(self, output_dir: Path = STROKE_SAMPLE_DIR) -> None:
        """Initialise the generator with an empty in-memory cache.

        Args:
            output_dir (Path): Directory where generated PNG files are saved.
                Defaults to ``STROKE_SAMPLE_DIR`` (``src/datafiles/stroke_samples/``).
                The directory is created if it does not already exist.
        """
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
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

        disk_path = self._output_dir / f"{stroke_type}.png"
        if disk_path.exists():
            image_bytes = disk_path.read_bytes()
            self._cache[stroke_type] = image_bytes
            logger.debug(
                "Loaded sample image for '%s' from disk (%d bytes)",
                stroke_type,
                len(image_bytes),
            )
            return image_bytes

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

        disk_path.write_bytes(image_bytes)
        logger.info(
            "Saved sample image for '%s' to %s (%d bytes, %d strokes)",
            stroke_type,
            disk_path,
            len(image_bytes),
            STROKES_PER_SAMPLE,
        )

        self._cache[stroke_type] = image_bytes
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
            "dry-brush": self._generate_dry_brush_samples,
            "chalk": self._generate_chalk_samples,
            "wet-brush": self._generate_wet_brush_samples,
            "burn": self._generate_burn_samples,
            "dodge": self._generate_dodge_samples,
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

    def _generate_dry_brush_samples(self) -> list[Stroke]:
        """Generate 5 varied dry-brush strokes for the sample canvas.

        Variations cover different brush_width values (10–60), bristle_count
        values (5–15), gap_probability values (0.1–0.5), and polyline paths
        with varying lengths and shapes spread across the 200×100 canvas.

        Returns:
            list[Stroke]: List of 5 dry-brush Stroke dicts.
        """
        return [
            # Wide, dense bristles, low gaps — red
            Stroke(
                type="dry-brush",
                color_hex="#CC0000",
                thickness=15,
                opacity=0.9,
                points=[[10, 20], [80, 30], [150, 15]],
                brush_width=50,
                bristle_count=15,
                gap_probability=0.15,
            ),
            # Medium width, medium bristles — blue
            Stroke(
                type="dry-brush",
                color_hex="#0044CC",
                thickness=10,
                opacity=0.8,
                points=[[20, 50], [100, 60], [180, 55]],
                brush_width=30,
                bristle_count=10,
                gap_probability=0.3,
            ),
            # Narrow, sparse bristles, high gaps — green
            Stroke(
                type="dry-brush",
                color_hex="#226622",
                thickness=8,
                opacity=0.7,
                points=[[190, 80], [120, 75], [30, 85]],
                brush_width=15,
                bristle_count=6,
                gap_probability=0.5,
            ),
            # Wide, few bristles — orange
            Stroke(
                type="dry-brush",
                color_hex="#FF8800",
                thickness=12,
                opacity=0.85,
                points=[[40, 10], [40, 40], [90, 50], [140, 45]],
                brush_width=40,
                bristle_count=5,
                gap_probability=0.25,
            ),
            # Medium, many bristles, moderate gaps — purple
            Stroke(
                type="dry-brush",
                color_hex="#7700AA",
                thickness=10,
                opacity=0.75,
                points=[[60, 90], [120, 85], [170, 90]],
                brush_width=25,
                bristle_count=12,
                gap_probability=0.35,
            ),
        ]

    def _generate_wet_brush_samples(self) -> list[Stroke]:
        """Generate 5 varied wet-brush strokes for the sample canvas.

        Variations cover different softness values (``MIN_SOFTNESS``–
        ``MAX_SOFTNESS``), flow values (``MIN_FLOW``–``MAX_FLOW``), and
        polyline paths with varying lengths and shapes spread across the
        200×100 canvas. The resulting images demonstrate the soft, bleeding
        edge characteristic of this stroke type.

        Returns:
            list[Stroke]: List of 5 wet-brush Stroke dicts.
        """
        # Clamp convenience values to configured limits.
        low_softness = max(MIN_SOFTNESS, 2)
        mid_softness = (MIN_SOFTNESS + MAX_SOFTNESS) // 2  # ~15
        high_softness = min(MAX_SOFTNESS, 25)
        low_flow = max(MIN_FLOW, 0.3)
        high_flow = min(MAX_FLOW, 0.95)

        return [
            # Soft, high-flow — red horizontal sweep
            Stroke(
                type="wet-brush",
                color_hex="#CC0000",
                thickness=12,
                opacity=0.8,
                points=[[10, 20], [80, 25], [150, 18]],
                softness=high_softness,
                flow=high_flow,
            ),
            # Medium softness, medium flow — blue diagonal
            Stroke(
                type="wet-brush",
                color_hex="#0044CC",
                thickness=10,
                opacity=0.7,
                points=[[20, 50], [90, 40], [170, 60]],
                softness=mid_softness,
                flow=0.6,
            ),
            # Low softness, low flow — green (sharper edge)
            Stroke(
                type="wet-brush",
                color_hex="#226622",
                thickness=8,
                opacity=0.9,
                points=[[180, 80], [120, 72], [40, 82]],
                softness=low_softness,
                flow=low_flow,
            ),
            # High softness, low flow — orange (wide bleed, translucent)
            Stroke(
                type="wet-brush",
                color_hex="#FF8800",
                thickness=15,
                opacity=0.6,
                points=[[30, 10], [70, 35], [130, 28], [175, 40]],
                softness=high_softness,
                flow=low_flow,
            ),
            # Medium softness, high flow — purple
            Stroke(
                type="wet-brush",
                color_hex="#7700AA",
                thickness=10,
                opacity=0.75,
                points=[[60, 88], [120, 82], [175, 90]],
                softness=mid_softness,
                flow=high_flow,
            ),
        ]

    def _generate_chalk_samples(self) -> list[Stroke]:
        """Generate 5 varied chalk strokes for the sample canvas.

        Variations cover different chalk_width values (5–30), grain_density
        values (2–6), and polyline paths with varying lengths and shapes
        spread across the 200×100 canvas.

        Returns:
            list[Stroke]: List of 5 chalk Stroke dicts.
        """
        return [
            # Wide chalk, dense grain — red
            Stroke(
                type="chalk",
                color_hex="#CC0000",
                thickness=1,
                opacity=0.85,
                points=[[10, 15], [60, 20], [110, 18]],
                chalk_width=28,
                grain_density=6,
            ),
            # Medium chalk, medium grain — blue
            Stroke(
                type="chalk",
                color_hex="#0044CC",
                thickness=1,
                opacity=0.75,
                points=[[20, 45], [90, 50], [160, 48]],
                chalk_width=18,
                grain_density=4,
            ),
            # Narrow chalk, light grain — green
            Stroke(
                type="chalk",
                color_hex="#226622",
                thickness=1,
                opacity=0.9,
                points=[[180, 75], [120, 78], [50, 72]],
                chalk_width=8,
                grain_density=2,
            ),
            # Wide chalk, light grain — orange
            Stroke(
                type="chalk",
                color_hex="#FF8800",
                thickness=1,
                opacity=0.8,
                points=[[30, 25], [80, 35], [130, 30], [175, 35]],
                chalk_width=22,
                grain_density=3,
            ),
            # Medium chalk, very dense grain — purple
            Stroke(
                type="chalk",
                color_hex="#7700AA",
                thickness=1,
                opacity=0.7,
                points=[[70, 85], [130, 88], [180, 85]],
                chalk_width=15,
                grain_density=5,
            ),
        ]

    def _generate_burn_samples(self) -> list[Stroke]:
        """Generate 5 varied burn strokes for the sample canvas.

        Variations cover different ``radius`` values (``MIN_BURN_DODGE_RADIUS``–
        ``MAX_BURN_DODGE_RADIUS``) and ``intensity`` values
        (``MIN_BURN_DODGE_INTENSITY``–``MAX_BURN_DODGE_INTENSITY``) spread
        across the 200×100 canvas.  ``color_hex`` and ``thickness`` are
        structurally required by the ``Stroke`` TypedDict but are ignored
        during burn rendering.

        Returns:
            list[Stroke]: List of 5 burn ``Stroke`` dicts.
        """
        low_radius = max(MIN_BURN_DODGE_RADIUS, 10)
        mid_radius = (MIN_BURN_DODGE_RADIUS + MAX_BURN_DODGE_RADIUS) // 2  # ~152
        high_radius = min(MAX_BURN_DODGE_RADIUS, 60)

        low_intensity = max(MIN_BURN_DODGE_INTENSITY, 0.1)
        mid_intensity = (MIN_BURN_DODGE_INTENSITY + MAX_BURN_DODGE_INTENSITY) / 2  # ~0.425
        high_intensity = min(MAX_BURN_DODGE_INTENSITY, 0.75)

        return [
            # Small radius, high intensity — top-left corner shadow
            Stroke(
                type="burn",
                color_hex="#000000",
                thickness=1,
                opacity=1.0,
                center_x=30,
                center_y=25,
                radius=high_radius,
                intensity=high_intensity,
            ),
            # Medium radius, medium intensity — centre
            Stroke(
                type="burn",
                color_hex="#333333",
                thickness=1,
                opacity=1.0,
                center_x=100,
                center_y=50,
                radius=mid_radius,
                intensity=mid_intensity,
            ),
            # Small radius, low intensity — top-right
            Stroke(
                type="burn",
                color_hex="#666666",
                thickness=1,
                opacity=1.0,
                center_x=170,
                center_y=20,
                radius=low_radius,
                intensity=low_intensity,
            ),
            # Large radius, high intensity — vignette-style bottom
            Stroke(
                type="burn",
                color_hex="#000000",
                thickness=1,
                opacity=1.0,
                center_x=100,
                center_y=90,
                radius=min(MAX_BURN_DODGE_RADIUS, 80),
                intensity=high_intensity,
            ),
            # Medium radius, high intensity — bottom-right
            Stroke(
                type="burn",
                color_hex="#222222",
                thickness=1,
                opacity=1.0,
                center_x=165,
                center_y=75,
                radius=high_radius,
                intensity=high_intensity,
            ),
        ]

    def _generate_dodge_samples(self) -> list[Stroke]:
        """Generate 5 varied dodge strokes for the sample canvas.

        Variations cover different ``radius`` values (``MIN_BURN_DODGE_RADIUS``–
        ``MAX_BURN_DODGE_RADIUS``) and ``intensity`` values
        (``MIN_BURN_DODGE_INTENSITY``–``MAX_BURN_DODGE_INTENSITY``) spread
        across the 200×100 canvas.  ``color_hex`` and ``thickness`` are
        structurally required by the ``Stroke`` TypedDict but are ignored
        during dodge rendering.

        Returns:
            list[Stroke]: List of 5 dodge ``Stroke`` dicts.
        """
        low_radius = max(MIN_BURN_DODGE_RADIUS, 10)
        mid_radius = (MIN_BURN_DODGE_RADIUS + MAX_BURN_DODGE_RADIUS) // 2  # ~152
        high_radius = min(MAX_BURN_DODGE_RADIUS, 60)

        low_intensity = max(MIN_BURN_DODGE_INTENSITY, 0.1)
        mid_intensity = (MIN_BURN_DODGE_INTENSITY + MAX_BURN_DODGE_INTENSITY) / 2  # ~0.425
        high_intensity = min(MAX_BURN_DODGE_INTENSITY, 0.75)

        return [
            # Small radius, high intensity — top-left highlight
            Stroke(
                type="dodge",
                color_hex="#ffffff",
                thickness=1,
                opacity=1.0,
                center_x=30,
                center_y=25,
                radius=high_radius,
                intensity=high_intensity,
            ),
            # Medium radius, medium intensity — centre
            Stroke(
                type="dodge",
                color_hex="#cccccc",
                thickness=1,
                opacity=1.0,
                center_x=100,
                center_y=50,
                radius=mid_radius,
                intensity=mid_intensity,
            ),
            # Small radius, low intensity — top-right
            Stroke(
                type="dodge",
                color_hex="#999999",
                thickness=1,
                opacity=1.0,
                center_x=170,
                center_y=20,
                radius=low_radius,
                intensity=low_intensity,
            ),
            # Large radius, high intensity — bright spot bottom
            Stroke(
                type="dodge",
                color_hex="#ffffff",
                thickness=1,
                opacity=1.0,
                center_x=100,
                center_y=90,
                radius=min(MAX_BURN_DODGE_RADIUS, 80),
                intensity=high_intensity,
            ),
            # Medium radius, high intensity — bottom-right highlight
            Stroke(
                type="dodge",
                color_hex="#dddddd",
                thickness=1,
                opacity=1.0,
                center_x=165,
                center_y=75,
                radius=high_radius,
                intensity=high_intensity,
            ),
        ]
