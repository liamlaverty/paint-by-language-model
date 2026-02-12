/**
 * Unit tests for prng.ts - Seeded PRNG utilities
 */

import { mulberry32 } from '@/lib/prng';

describe('mulberry32', () => {
  it('should return a function that generates pseudo-random numbers', () => {
    const rng = mulberry32(12345);
    expect(typeof rng).toBe('function');

    const result = rng();
    expect(typeof result).toBe('number');
  });

  it('should generate numbers in the range [0, 1)', () => {
    const rng = mulberry32(12345);

    for (let i = 0; i < 100; i++) {
      const result = rng();
      expect(result).toBeGreaterThanOrEqual(0);
      expect(result).toBeLessThan(1);
    }
  });

  it('should produce deterministic sequences for the same seed', () => {
    const rng1 = mulberry32(54321);
    const rng2 = mulberry32(54321);

    const sequence1 = Array.from({ length: 10 }, () => rng1());
    const sequence2 = Array.from({ length: 10 }, () => rng2());

    expect(sequence1).toEqual(sequence2);
  });

  it('should produce different sequences for different seeds', () => {
    const rng1 = mulberry32(11111);
    const rng2 = mulberry32(22222);

    const sequence1 = Array.from({ length: 10 }, () => rng1());
    const sequence2 = Array.from({ length: 10 }, () => rng2());

    expect(sequence1).not.toEqual(sequence2);
  });

  it('should handle seed value of 0', () => {
    const rng = mulberry32(0);
    const result = rng();

    expect(typeof result).toBe('number');
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThan(1);
  });

  it('should handle negative seed values', () => {
    const rng = mulberry32(-12345);
    const result = rng();

    expect(typeof result).toBe('number');
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThan(1);
  });

  it('should produce a uniform-ish distribution', () => {
    const rng = mulberry32(99999);
    const samples = 10000;
    const bins = 10;
    const counts = new Array(bins).fill(0);

    for (let i = 0; i < samples; i++) {
      const value = rng();
      const binIndex = Math.floor(value * bins);
      counts[binIndex]++;
    }

    // Each bin should have roughly samples/bins values (1000 ± some tolerance)
    const expected = samples / bins;
    const tolerance = expected * 0.2; // 20% tolerance

    counts.forEach((count) => {
      expect(count).toBeGreaterThan(expected - tolerance);
      expect(count).toBeLessThan(expected + tolerance);
    });
  });

  it('should maintain state across calls', () => {
    const rng = mulberry32(42);

    const first = rng();
    const second = rng();
    const third = rng();

    expect(first).not.toBe(second);
    expect(second).not.toBe(third);
    expect(first).not.toBe(third);
  });
});
