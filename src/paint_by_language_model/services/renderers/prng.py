"""Seeded pseudo-random number generator utilities for deterministic rendering."""

from collections.abc import Callable


def _to_int32(n: int) -> int:
    """
    Convert a number to a 32-bit signed integer (matching JavaScript `| 0` behavior).

    Args:
        n (int): Input number

    Returns:
        int: n converted to a 32-bit signed integer (-2147483648 to 2147483647)
    """
    n = n & 0xFFFFFFFF  # Mask to 32 bits
    if n >= 0x80000000:  # If high bit set, it's negative in two's complement
        n -= 0x100000000
    return n


def _imul(a: int, b: int) -> int:
    """
    32-bit signed integer multiplication (matching JavaScript Math.imul).

    Args:
        a (int): First operand
        b (int): Second operand

    Returns:
        int: Product as 32-bit signed integer
    """
    return _to_int32(a * b)


def mulberry32(seed: int) -> Callable[[], float]:
    """
    Mulberry32 seeded PRNG matching the TypeScript viewer implementation.

    Returns a generator function that produces deterministic pseudo-random
    numbers in the range [0, 1) based on the provided seed. Each call to
    the returned function advances the internal state.

    This implementation produces identical output to the TypeScript mulberry32
    in src/viewer/src/lib/prng.ts for any given seed, ensuring deterministic
    rendering across Python backend and viewer frontend.

    Args:
        seed (int): Integer seed value. Different seeds produce different
            random sequences.

    Returns:
        Callable[[], float]: A callable that returns the next random float
            in [0, 1) on each call. Each invocation advances the internal state.

    Example:
        >>> rng = mulberry32(12345)
        >>> first_random = rng()   # 0.6536078453063965
        >>> second_random = rng()  # 0.2703539133071899
        >>> # Same seed always produces same sequence
        >>> rng2 = mulberry32(12345)
        >>> rng2() == first_random  # True
    """
    # Use list for mutable closure state
    state = _to_int32(seed)
    state_list = [state]

    def next_float() -> float:
        """Generate the next random float in the sequence.

        Returns:
            float: Pseudo-random value in [0, 1)
        """
        # Equivalent to: seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
        state_list[0] = _to_int32(state_list[0] + 0x6D2B79F5)

        seed_val = state_list[0]

        # Convert to unsigned for right shifts (>>> in JavaScript)
        unsigned_seed = seed_val & 0xFFFFFFFF

        # t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
        t = _imul(unsigned_seed ^ (unsigned_seed >> 15), 1 | seed_val)

        # t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
        unsigned_t = t & 0xFFFFFFFF
        t = _to_int32(t + _imul(unsigned_t ^ (unsigned_t >> 7), 61 | t)) ^ t

        # return ((t ^ (t >>> 14)) >>> 0) / 4294967296
        unsigned_t_final = t & 0xFFFFFFFF
        result = (unsigned_t_final ^ (unsigned_t_final >> 14)) & 0xFFFFFFFF

        return result / 0x100000000

    return next_float
