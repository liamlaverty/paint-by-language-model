"""Stroke sample image generator for VLM prompt visual context."""

import json
import logging
from pathlib import Path
from typing import cast

from config import (
    STROKE_SAMPLE_BACKGROUND,
    STROKE_SAMPLE_DIR,
    STROKE_SAMPLE_HEIGHT,
    STROKE_SAMPLE_WIDTH,
    STROKES_PER_SAMPLE,
)
from models.stroke import Stroke
from services.canvas_manager import CanvasManager

logger = logging.getLogger(__name__)

# Path to the JSON file containing stroke sample data.
_SAMPLE_DATA_PATH: Path = Path(__file__).parent.parent.parent / "datafiles" / "stroke_samples.json"

# Supported stroke types — kept as an explicit constant for external consumers.
# A validation assertion in StrokeSampleGenerator.__init__ ensures this list
# stays in sync with the JSON file.
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
        """Initialise the generator, load stroke sample data from JSON, and validate it.

        Loads ``stroke_samples.json`` from the datafiles directory and asserts that
        every stroke type has exactly ``STROKES_PER_SAMPLE`` entries.  Also asserts
        that the JSON keys match ``SUPPORTED_STROKE_TYPES`` so the two stay in sync.

        Args:
            output_dir (Path): Directory where generated PNG files are saved.
                Defaults to ``STROKE_SAMPLE_DIR`` (``src/datafiles/stroke_samples/``).
                The directory is created if it does not already exist.

        Raises:
            AssertionError: If the JSON data does not contain exactly
                ``STROKES_PER_SAMPLE`` entries for each stroke type, or if the
                JSON keys do not match ``SUPPORTED_STROKE_TYPES``.
            FileNotFoundError: If ``stroke_samples.json`` does not exist.
        """
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, bytes] = {}

        raw: dict[str, list[dict[str, object]]] = json.loads(
            _SAMPLE_DATA_PATH.read_text(encoding="utf-8")
        )
        self._sample_data: dict[str, list[Stroke]] = {
            stype: [cast(Stroke, entry) for entry in strokes] for stype, strokes in raw.items()
        }

        for stype, strokes in self._sample_data.items():
            assert len(strokes) == STROKES_PER_SAMPLE, (
                f"stroke_samples.json: expected {STROKES_PER_SAMPLE} samples for '{stype}', "
                f"got {len(strokes)}"
            )

        assert set(self._sample_data.keys()) == set(SUPPORTED_STROKE_TYPES), (
            f"stroke_samples.json keys {sorted(self._sample_data.keys())} do not match "
            f"SUPPORTED_STROKE_TYPES {sorted(SUPPORTED_STROKE_TYPES)}"
        )

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
        """Return the pre-loaded sample strokes for the given stroke type.

        Args:
            stroke_type (str): Stroke type name (must be a key in ``_sample_data``).

        Returns:
            list[Stroke]: A list of ``STROKES_PER_SAMPLE`` Stroke dicts loaded
                from ``stroke_samples.json``.
        """
        return list(self._sample_data[stroke_type])
