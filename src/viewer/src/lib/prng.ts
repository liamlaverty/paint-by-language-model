/**
 * Seeded pseudo-random number generator (PRNG) utilities.
 *
 * This module provides the Mulberry32 algorithm for deterministic random
 * number generation. Used by the splatter renderer to ensure consistent
 * dot placement across viewer sessions.
 */

/**
 * Mulberry32 seeded pseudo-random number generator.
 *
 * Returns a generator function that produces deterministic pseudo-random
 * numbers in the range [0, 1) based on the provided seed. Each call to
 * the returned function advances the internal state.
 *
 * Used by the splatter renderer to generate reproducible dot patterns.
 * The same seed will always produce the same sequence of random numbers.
 *
 * @param {number} seed - Initial seed value (integer). Different seeds
 *   produce different sequences.
 * @returns {() => number} Function that generates the next random number
 *   in the sequence (0.0 to 1.0, exclusive of 1.0)
 *
 * @example
 * const rng = mulberry32(12345);
 * const firstRandom = rng();  // 0.6536078453063965
 * const secondRandom = rng(); // 0.2703539133071899
 */
export function mulberry32(seed: number): () => number {
  return function (): number {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
