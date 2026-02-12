/**
 * Unit tests for color-utils.ts - Color conversion and encoding utilities
 */

import { hexToRGBA, strokeIndexToColor, colorToStrokeIndex } from '@/lib/color-utils';

describe('hexToRGBA', () => {
  it('should convert 6-digit hex color to RGBA with given opacity', () => {
    const result = hexToRGBA('#FF5733', 0.5);
    expect(result).toBe('rgba(255,87,51,0.5)');
  });

  it('should convert 6-digit hex color without # prefix', () => {
    const result = hexToRGBA('FF5733', 0.8);
    expect(result).toBe('rgba(255,87,51,0.8)');
  });

  it('should handle 8-digit hex color with alpha channel', () => {
    const result = hexToRGBA('#FF5733CC', 1.0);
    // CC in hex = 204 / 255 = 0.8
    expect(result).toBe('rgba(255,87,51,0.8)');
  });

  it('should handle 8-digit hex color without # prefix', () => {
    const result = hexToRGBA('FF573380', 1.0);
    // 80 in hex = 128 / 255 ≈ 0.5019607843137255
    expect(result).toBe('rgba(255,87,51,0.5019607843137255)');
  });

  it('should handle black color', () => {
    const result = hexToRGBA('#000000', 1.0);
    expect(result).toBe('rgba(0,0,0,1)');
  });

  it('should handle white color', () => {
    const result = hexToRGBA('#FFFFFF', 0.75);
    expect(result).toBe('rgba(255,255,255,0.75)');
  });

  it('should handle opacity of 0', () => {
    const result = hexToRGBA('#FF5733', 0);
    expect(result).toBe('rgba(255,87,51,0)');
  });

  it('should handle opacity of 1', () => {
    const result = hexToRGBA('#FF5733', 1);
    expect(result).toBe('rgba(255,87,51,1)');
  });
});

describe('strokeIndexToColor', () => {
  it('should encode index 0 as rgb(0,0,1)', () => {
    const result = strokeIndexToColor(0);
    expect(result).toBe('rgb(0,0,1)');
  });

  it('should encode index 1 as rgb(0,0,2)', () => {
    const result = strokeIndexToColor(1);
    expect(result).toBe('rgb(0,0,2)');
  });

  it('should encode index 255 as rgb(0,1,0)', () => {
    const result = strokeIndexToColor(255);
    expect(result).toBe('rgb(0,1,0)');
  });

  it('should encode index 256 as rgb(0,1,1)', () => {
    const result = strokeIndexToColor(256);
    expect(result).toBe('rgb(0,1,1)');
  });

  it('should encode index 65535 as rgb(1,0,0)', () => {
    const result = strokeIndexToColor(65535);
    expect(result).toBe('rgb(1,0,0)');
  });

  it('should encode index 65536 as rgb(1,0,1)', () => {
    const result = strokeIndexToColor(65536);
    expect(result).toBe('rgb(1,0,1)');
  });

  it('should encode large index correctly', () => {
    const result = strokeIndexToColor(16777214); // Max value: 2^24 - 2
    expect(result).toBe('rgb(255,255,255)');
  });

  it('should handle sequential indices distinctly', () => {
    const colors = Array.from({ length: 10 }, (_, i) => strokeIndexToColor(i));
    const uniqueColors = new Set(colors);
    expect(uniqueColors.size).toBe(10);
  });
});

describe('colorToStrokeIndex', () => {
  it('should decode rgb(0,0,0) as -1 (background)', () => {
    const result = colorToStrokeIndex(0, 0, 0);
    expect(result).toBe(-1);
  });

  it('should decode rgb(0,0,1) as index 0', () => {
    const result = colorToStrokeIndex(0, 0, 1);
    expect(result).toBe(0);
  });

  it('should decode rgb(0,0,2) as index 1', () => {
    const result = colorToStrokeIndex(0, 0, 2);
    expect(result).toBe(1);
  });

  it('should decode rgb(0,1,0) as index 255', () => {
    const result = colorToStrokeIndex(0, 1, 0);
    expect(result).toBe(255);
  });

  it('should decode rgb(1,0,0) as index 65535', () => {
    const result = colorToStrokeIndex(1, 0, 0);
    expect(result).toBe(65535);
  });

  it('should decode rgb(255,255,255) correctly', () => {
    const result = colorToStrokeIndex(255, 255, 255);
    expect(result).toBe(16777214); // 2^24 - 2
  });

  it('should be inverse of strokeIndexToColor', () => {
    const testIndices = [0, 1, 42, 255, 256, 1000, 65535, 65536, 100000];

    testIndices.forEach((index) => {
      const color = strokeIndexToColor(index);
      const matches = color.match(/rgb\((\d+),(\d+),(\d+)\)/);
      expect(matches).not.toBeNull();

      if (matches) {
        const r = parseInt(matches[1], 10);
        const g = parseInt(matches[2], 10);
        const b = parseInt(matches[3], 10);
        const decoded = colorToStrokeIndex(r, g, b);
        expect(decoded).toBe(index);
      }
    });
  });

  it('should handle maximum RGB values', () => {
    const result = colorToStrokeIndex(255, 255, 255);
    expect(result).toBeGreaterThan(0);
  });
});

describe('strokeIndexToColor and colorToStrokeIndex round-trip', () => {
  it('should encode and decode consistently for various indices', () => {
    const testCases = [0, 1, 10, 100, 255, 256, 1000, 10000, 65535, 65536, 100000];

    testCases.forEach((originalIndex) => {
      const encoded = strokeIndexToColor(originalIndex);
      const matches = encoded.match(/rgb\((\d+),(\d+),(\d+)\)/);

      if (matches) {
        const r = parseInt(matches[1], 10);
        const g = parseInt(matches[2], 10);
        const b = parseInt(matches[3], 10);
        const decoded = colorToStrokeIndex(r, g, b);

        expect(decoded).toBe(originalIndex);
      }
    });
  });
});
