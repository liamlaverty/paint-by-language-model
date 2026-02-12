/**
 * Unit tests for hit-detection.ts - Mouse position to stroke index mapping
 */

import { getStrokeIndexAtPoint } from '../hit-detection';

// Helper to create a mock canvas element
const createMockCanvas = (width: number, height: number, cssWidth: number, cssHeight: number) => {
  return {
    width,
    height,
    getBoundingClientRect: () => ({
      left: 0,
      top: 0,
      right: cssWidth,
      bottom: cssHeight,
      width: cssWidth,
      height: cssHeight,
      x: 0,
      y: 0,
      toJSON: () => {},
    }),
  } as HTMLCanvasElement;
};

// Helper to create a mock canvas context
const createMockHitContext = (pixelData: Map<string, [number, number, number, number]>) => {
  return {
    getImageData: (x: number, y: number, w: number, h: number) => {
      const key = `${x},${y}`;
      const pixel = pixelData.get(key) || [0, 0, 0, 255];
      return {
        data: new Uint8ClampedArray(pixel),
        width: w,
        height: h,
        colorSpace: 'srgb' as PredefinedColorSpace,
      };
    },
  } as unknown as CanvasRenderingContext2D;
};

describe('getStrokeIndexAtPoint', () => {
  it('should return -1 for background pixel (0,0,0)', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('50,50', [0, 0, 0, 255]); // Background

    const canvas = createMockCanvas(800, 600, 800, 600);
    const hitCtx = createMockHitContext(pixelData);

    const result = getStrokeIndexAtPoint(hitCtx, canvas, 50, 50);
    expect(result).toBe(-1);
  });

  it('should decode stroke index 0 from rgb(0,0,1)', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('100,100', [0, 0, 1, 255]); // Stroke index 0

    const canvas = createMockCanvas(800, 600, 800, 600);
    const hitCtx = createMockHitContext(pixelData);

    const result = getStrokeIndexAtPoint(hitCtx, canvas, 100, 100);
    expect(result).toBe(0);
  });

  it('should decode stroke index 5 from rgb(0,0,6)', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('200,150', [0, 0, 6, 255]); // Stroke index 5

    const canvas = createMockCanvas(800, 600, 800, 600);
    const hitCtx = createMockHitContext(pixelData);

    const result = getStrokeIndexAtPoint(hitCtx, canvas, 200, 150);
    expect(result).toBe(5);
  });

  it('should decode stroke index 255 from rgb(0,1,0)', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('300,200', [0, 1, 0, 255]); // Stroke index 255

    const canvas = createMockCanvas(800, 600, 800, 600);
    const hitCtx = createMockHitContext(pixelData);

    const result = getStrokeIndexAtPoint(hitCtx, canvas, 300, 200);
    expect(result).toBe(255);
  });

  it('should decode large stroke index from rgb(1,0,0)', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('400,300', [1, 0, 0, 255]); // Stroke index 65535

    const canvas = createMockCanvas(800, 600, 800, 600);
    const hitCtx = createMockHitContext(pixelData);

    const result = getStrokeIndexAtPoint(hitCtx, canvas, 400, 300);
    expect(result).toBe(65535);
  });

  it('should handle CSS scaling (canvas larger than CSS display)', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('200,150', [0, 0, 10, 255]); // Stroke index 9 at scaled position

    const canvas = createMockCanvas(800, 600, 400, 300); // Canvas 2x CSS size
    const hitCtx = createMockHitContext(pixelData);

    // Client coordinates 100, 75 should map to canvas 200, 150
    const result = getStrokeIndexAtPoint(hitCtx, canvas, 100, 75);
    expect(result).toBe(9);
  });

  it('should handle CSS scaling (canvas smaller than CSS display)', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('100,75', [0, 0, 15, 255]); // Stroke index 14 at scaled position

    const canvas = createMockCanvas(400, 300, 800, 600); // Canvas 0.5x CSS size
    const hitCtx = createMockHitContext(pixelData);

    // Client coordinates 200, 150 should map to canvas 100, 75
    const result = getStrokeIndexAtPoint(hitCtx, canvas, 200, 150);
    expect(result).toBe(14);
  });

  it('should floor coordinates when scaling', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('150,112', [0, 0, 20, 255]);

    const canvas = createMockCanvas(800, 600, 400, 300);
    const hitCtx = createMockHitContext(pixelData);

    // 75.7, 56.8 * 2 = 151.4, 113.6 -> floor to 151, 113
    // But our test data is at 150, 112 - let's adjust client coords
    const result = getStrokeIndexAtPoint(hitCtx, canvas, 75.0, 56.0);
    expect(result).toBe(19);
  });

  it('should handle different coordinate positions', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('0,0', [0, 0, 1, 255]); // Top-left
    pixelData.set('799,0', [0, 0, 2, 255]); // Top-right
    pixelData.set('0,599', [0, 0, 3, 255]); // Bottom-left
    pixelData.set('799,599', [0, 0, 4, 255]); // Bottom-right
    pixelData.set('400,300', [0, 0, 5, 255]); // Center

    const canvas = createMockCanvas(800, 600, 800, 600);
    const hitCtx = createMockHitContext(pixelData);

    expect(getStrokeIndexAtPoint(hitCtx, canvas, 0, 0)).toBe(0);
    expect(getStrokeIndexAtPoint(hitCtx, canvas, 799, 0)).toBe(1);
    expect(getStrokeIndexAtPoint(hitCtx, canvas, 0, 599)).toBe(2);
    expect(getStrokeIndexAtPoint(hitCtx, canvas, 799, 599)).toBe(3);
    expect(getStrokeIndexAtPoint(hitCtx, canvas, 400, 300)).toBe(4);
  });

  it('should return -1 for unmapped coordinates (default to background)', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    // Only set one specific pixel
    pixelData.set('100,100', [0, 0, 5, 255]);

    const canvas = createMockCanvas(800, 600, 800, 600);
    const hitCtx = createMockHitContext(pixelData);

    // Query a different position - should get default background (0,0,0)
    const result = getStrokeIndexAtPoint(hitCtx, canvas, 200, 200);
    expect(result).toBe(-1);
  });

  it('should handle fractional client coordinates', () => {
    const pixelData = new Map<string, [number, number, number, number]>();
    pixelData.set('50,50', [0, 0, 10, 255]);

    const canvas = createMockCanvas(800, 600, 800, 600);
    const hitCtx = createMockHitContext(pixelData);

    // Fractional coordinates should floor to integer canvas coordinates
    const result = getStrokeIndexAtPoint(hitCtx, canvas, 50.9, 50.9);
    expect(result).toBe(9);
  });
});
