"""Unit tests for StrokeSampleGenerator service."""

import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.stroke_sample_generator import (
    SUPPORTED_STROKE_TYPES,
    StrokeSampleGenerator,
)


@pytest.fixture()
def generator() -> StrokeSampleGenerator:
    """Return a fresh StrokeSampleGenerator for each test.

    Returns:
        StrokeSampleGenerator: A new instance with an empty cache.
    """
    return StrokeSampleGenerator()


# ---------------------------------------------------------------------------
# test_generate_all_samples_returns_all_types
# ---------------------------------------------------------------------------


def test_generate_all_samples_returns_all_types(
    generator: StrokeSampleGenerator,
) -> None:
    """generate_all_samples() must return a dict with all 5 stroke type keys.

    Args:
        generator (StrokeSampleGenerator): Fresh generator fixture.
    """
    samples = generator.generate_all_samples()
    expected_keys = {"line", "arc", "polyline", "circle", "splatter"}
    assert set(samples.keys()) == expected_keys


# ---------------------------------------------------------------------------
# test_sample_image_dimensions
# ---------------------------------------------------------------------------


def test_sample_image_dimensions(generator: StrokeSampleGenerator) -> None:
    """Each sample PNG must decode to a 200×100 image.

    Args:
        generator (StrokeSampleGenerator): Fresh generator fixture.
    """
    samples = generator.generate_all_samples()
    for stroke_type, image_bytes in samples.items():
        img = Image.open(io.BytesIO(image_bytes))
        assert img.size == (200, 100), (
            f"Sample for '{stroke_type}' has wrong size {img.size}, expected (200, 100)"
        )


# ---------------------------------------------------------------------------
# test_sample_image_format
# ---------------------------------------------------------------------------


def test_sample_image_format(generator: StrokeSampleGenerator) -> None:
    """Each sample value must be valid PNG bytes (PNG magic bytes prefix).

    Args:
        generator (StrokeSampleGenerator): Fresh generator fixture.
    """
    png_magic = b"\x89PNG"
    samples = generator.generate_all_samples()
    for stroke_type, image_bytes in samples.items():
        assert isinstance(image_bytes, bytes), (
            f"Sample for '{stroke_type}' is not bytes, got {type(image_bytes).__name__}"
        )
        assert image_bytes[:4] == png_magic, (
            f"Sample for '{stroke_type}' does not start with PNG magic bytes"
        )


# ---------------------------------------------------------------------------
# test_samples_are_cached
# ---------------------------------------------------------------------------


def test_samples_are_cached(generator: StrokeSampleGenerator) -> None:
    """Calling generate_all_samples() twice must return identical bytes objects (identity).

    Args:
        generator (StrokeSampleGenerator): Fresh generator fixture.
    """
    first_call = generator.generate_all_samples()
    second_call = generator.generate_all_samples()
    for stroke_type in SUPPORTED_STROKE_TYPES:
        assert first_call[stroke_type] is second_call[stroke_type], (
            f"Cache did not return the same bytes object for stroke type '{stroke_type}'"
        )


# ---------------------------------------------------------------------------
# test_generate_sample_invalid_type
# ---------------------------------------------------------------------------


def test_generate_sample_invalid_type(generator: StrokeSampleGenerator) -> None:
    """generate_sample() must raise ValueError for an unrecognised stroke type.

    Args:
        generator (StrokeSampleGenerator): Fresh generator fixture.
    """
    with pytest.raises(ValueError, match="Unknown stroke type"):
        generator.generate_sample("blob")


# ---------------------------------------------------------------------------
# test_each_sample_has_visible_strokes
# ---------------------------------------------------------------------------


def test_each_sample_has_visible_strokes(generator: StrokeSampleGenerator) -> None:
    """Each rendered sample must contain pixels that differ from the uniform background.

    This verifies that strokes were actually painted onto the canvas.

    Args:
        generator (StrokeSampleGenerator): Fresh generator fixture.
    """
    # Background colour from config — decoded as RGB tuple
    bg_hex = "#F5F5F5"
    bg_r = int(bg_hex[1:3], 16)
    bg_g = int(bg_hex[3:5], 16)
    bg_b = int(bg_hex[5:7], 16)
    bg_array = np.array([bg_r, bg_g, bg_b], dtype=np.uint8)

    samples = generator.generate_all_samples()
    for stroke_type, image_bytes in samples.items():
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pixel_array = np.array(img)
        non_background_mask = np.any(pixel_array != bg_array, axis=-1)
        assert non_background_mask.any(), (
            f"Sample for '{stroke_type}' has no pixels that differ from the background — "
            "strokes do not appear to have been rendered"
        )
