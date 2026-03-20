"""Tests verifying that stroke prompt constraint ranges match config constants.

Prevents drift between the ranges advertised to the VLM in the prompt and
the ranges enforced by the renderer validators.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import (
    MAX_ARC_ANGLE,
    MAX_BRISTLE_COUNT,
    MAX_BRUSH_WIDTH,
    MAX_BURN_DODGE_INTENSITY,
    MAX_BURN_DODGE_RADIUS,
    MAX_CHALK_WIDTH,
    MAX_CIRCLE_RADIUS,
    MAX_DOT_SIZE,
    MAX_FLOW,
    MAX_GAP_PROBABILITY,
    MAX_GRAIN_DENSITY,
    MAX_POLYLINE_POINTS,
    MAX_SOFTNESS,
    MAX_SPLATTER_COUNT,
    MAX_SPLATTER_RADIUS,
    MIN_ARC_ANGLE,
    MIN_BRISTLE_COUNT,
    MIN_BRUSH_WIDTH,
    MIN_BURN_DODGE_INTENSITY,
    MIN_BURN_DODGE_RADIUS,
    MIN_CHALK_WIDTH,
    MIN_CIRCLE_RADIUS,
    MIN_DOT_SIZE,
    MIN_FLOW,
    MIN_GAP_PROBABILITY,
    MIN_GRAIN_DENSITY,
    MIN_POLYLINE_POINTS,
    MIN_SOFTNESS,
    MIN_SPLATTER_COUNT,
    MIN_SPLATTER_RADIUS,
)
from services.clients.stroke_vlm_client import StrokeVLMClient


@pytest.fixture
def stroke_types_section() -> str:
    """Build the stroke types section from a real StrokeVLMClient."""
    with patch("services.clients.stroke_vlm_client.VLMClient"):
        client = StrokeVLMClient(
            base_url="http://test.com",
            model="test-model",
            timeout=60,
            api_key="test_key",
            temperature=0.7,
        )
    return client._build_stroke_types_section()


class TestDryBrushConstraints:
    """Verify dry-brush prompt ranges match config."""

    def test_brush_width_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct brush_width range."""
        expected = f"brush_width ({MIN_BRUSH_WIDTH}-{MAX_BRUSH_WIDTH})"
        assert expected in stroke_types_section

    def test_bristle_count_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct bristle_count range."""
        expected = f"bristle_count ({MIN_BRISTLE_COUNT}-{MAX_BRISTLE_COUNT})"
        assert expected in stroke_types_section

    def test_gap_probability_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct gap_probability range."""
        expected = f"gap_probability ({MIN_GAP_PROBABILITY}-{MAX_GAP_PROBABILITY})"
        assert expected in stroke_types_section


class TestChalkConstraints:
    """Verify chalk prompt ranges match config."""

    def test_chalk_width_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct chalk_width range."""
        expected = f"chalk_width ({MIN_CHALK_WIDTH}-{MAX_CHALK_WIDTH})"
        assert expected in stroke_types_section

    def test_grain_density_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct grain_density range."""
        expected = f"grain_density ({MIN_GRAIN_DENSITY}-{MAX_GRAIN_DENSITY})"
        assert expected in stroke_types_section


class TestWetBrushConstraints:
    """Verify wet-brush prompt ranges match config."""

    def test_softness_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct softness range."""
        expected = f"softness ({MIN_SOFTNESS}-{MAX_SOFTNESS}"
        assert expected in stroke_types_section

    def test_flow_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct flow range."""
        expected = f"flow ({MIN_FLOW}-{MAX_FLOW}"
        assert expected in stroke_types_section


class TestBurnDodgeConstraints:
    """Verify burn and dodge prompt ranges match config."""

    def test_burn_radius_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct burn radius range."""
        expected = f"radius ({MIN_BURN_DODGE_RADIUS}-{MAX_BURN_DODGE_RADIUS})"
        assert expected in stroke_types_section

    def test_burn_intensity_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct burn intensity range."""
        expected = f"intensity ({MIN_BURN_DODGE_INTENSITY}-{MAX_BURN_DODGE_INTENSITY})"
        assert expected in stroke_types_section


class TestSplatterConstraints:
    """Verify splatter prompt ranges match config."""

    def test_splatter_radius_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct splatter_radius range."""
        expected = f"splatter_radius ({MIN_SPLATTER_RADIUS}-{MAX_SPLATTER_RADIUS})"
        assert expected in stroke_types_section

    def test_splatter_count_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct splatter_count range."""
        expected = f"splatter_count ({MIN_SPLATTER_COUNT}-{MAX_SPLATTER_COUNT})"
        assert expected in stroke_types_section

    def test_dot_size_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct dot_size range."""
        expected = f"dot_size_min ({MIN_DOT_SIZE}-{MAX_DOT_SIZE})"
        assert expected in stroke_types_section


class TestCircleConstraints:
    """Verify circle prompt ranges match config."""

    def test_circle_radius_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct circle radius range."""
        expected = f"radius ({MIN_CIRCLE_RADIUS}-{MAX_CIRCLE_RADIUS})"
        assert expected in stroke_types_section


class TestArcConstraints:
    """Verify arc prompt ranges match config."""

    def test_arc_angle_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct arc angle range."""
        expected = f"arc_start_angle ({MIN_ARC_ANGLE}-{MAX_ARC_ANGLE}"
        assert expected in stroke_types_section


class TestPolylineConstraints:
    """Verify polyline prompt ranges match config."""

    def test_polyline_points_range(self, stroke_types_section: str) -> None:
        """Prompt must advertise the correct polyline points range."""
        expected = f"points (list of [x,y] coordinates, {MIN_POLYLINE_POINTS}-{MAX_POLYLINE_POINTS} points)"
        assert expected in stroke_types_section
