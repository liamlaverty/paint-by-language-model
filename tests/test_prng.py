"""Tests for the mulberry32 seeded PRNG implementation.

This test suite validates that the Python mulberry32 implementation produces
identical output to the TypeScript version in src/viewer/src/lib/prng.ts.

Expected values were pre-computed by running the TypeScript implementation
with specific seeds.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.renderers.prng import mulberry32


class TestMulberry32:
    """Test suite for mulberry32 PRNG cross-validation."""

    def test_seed_0(self) -> None:
        """Test PRNG output for seed 0."""
        rng = mulberry32(0)
        expected = [
            0.2664292086847126,
            0.0003297457005829,
            0.2232720274478197,
            0.1462021479383111,
            0.4673278229311109,
            0.5450490827206522,
            0.6152513844426721,
            0.6489853798411787,
            0.4560072126332670,
            0.5812189676798880,
        ]
        for i, expected_value in enumerate(expected):
            actual = rng()
            assert abs(actual - expected_value) < 1e-15, (
                f"Seed 0: value {i} mismatch. "
                f"Expected {expected_value:.16f}, got {actual:.16f}"
            )

    def test_seed_42(self) -> None:
        """Test PRNG output for seed 42."""
        rng = mulberry32(42)
        expected = [
            0.6011037519201636,
            0.4482905589975417,
            0.8524657934904099,
            0.6697340414393693,
            0.1748138987459242,
            0.5265925421845168,
            0.2732279943302274,
            0.6247446539346129,
            0.8654746483080089,
            0.4723170551005751,
        ]
        for i, expected_value in enumerate(expected):
            actual = rng()
            assert abs(actual - expected_value) < 1e-15, (
                f"Seed 42: value {i} mismatch. "
                f"Expected {expected_value:.16f}, got {actual:.16f}"
            )

    def test_seed_large(self) -> None:
        """Test PRNG output for large seed (2654435761)."""
        rng = mulberry32(2654435761)
        expected = [
            0.5464560757391155,
            0.4595562904141843,
            0.2470416973810643,
            0.5192999374121428,
            0.8892884191591293,
            0.7024417922366410,
            0.4254938538651913,
            0.4705080981366336,
            0.6971602996345609,
            0.4754178524017334,
        ]
        for i, expected_value in enumerate(expected):
            actual = rng()
            assert abs(actual - expected_value) < 1e-15, (
                f"Seed 2654435761: value {i} mismatch. "
                f"Expected {expected_value:.16f}, got {actual:.16f}"
            )

    def test_seed_max_uint32(self) -> None:
        """Test PRNG output for maximum 32-bit unsigned integer (0xFFFFFFFF)."""
        rng = mulberry32(0xFFFFFFFF)
        expected = [
            0.8964226141106337,
            0.1894782567396760,
            0.7156526781618595,
            0.9440599093213677,
            0.8452364315744489,
            0.5391399988438934,
            0.6804977387655526,
            0.4755720964167267,
            0.1358577392529696,
            0.9884445976931602,
        ]
        for i, expected_value in enumerate(expected):
            actual = rng()
            assert abs(actual - expected_value) < 1e-15, (
                f"Seed 0xFFFFFFFF: value {i} mismatch. "
                f"Expected {expected_value:.16f}, got {actual:.16f}"
            )

    def test_determinism(self) -> None:
        """Test that same seed produces identical sequences."""
        seed = 999
        rng1 = mulberry32(seed)
        rng2 = mulberry32(seed)

        # Generate 20 values from each and verify they match
        for _ in range(20):
            assert rng1() == rng2(), "Same seed should produce identical sequences"

    def test_state_independence(self) -> None:
        """Test that different PRNG instances have independent state."""
        rng1 = mulberry32(100)
        rng2 = mulberry32(100)

        # Advance first generator
        for _ in range(5):
            rng1()

        # Second generator should still produce first value
        first_val_rng2 = rng2()

        # Create fresh generator and verify it matches
        rng3 = mulberry32(100)
        first_val_rng3 = rng3()

        assert first_val_rng2 == first_val_rng3, (
            "Independent PRNG instances should not affect each other's state"
        )

    def test_output_range(self) -> None:
        """Test that all outputs are in [0, 1) range."""
        rng = mulberry32(12345)
        for _ in range(1000):
            val = rng()
            assert 0.0 <= val < 1.0, f"PRNG value {val} outside valid range [0, 1)"

    def test_different_seeds_produce_different_sequences(self) -> None:
        """Test that different seeds produce different random sequences."""
        rng1 = mulberry32(1)
        rng2 = mulberry32(2)

        # Get first 10 values from each
        seq1 = [rng1() for _ in range(10)]
        seq2 = [rng2() for _ in range(10)]

        # Sequences should be different
        assert seq1 != seq2, "Different seeds should produce different sequences"
