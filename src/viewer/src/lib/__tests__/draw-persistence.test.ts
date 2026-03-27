/**
 * Unit tests for draw-persistence.ts - localStorage save/load and JSON export/import
 */

import {
  saveDrawing,
  loadDrawing,
  clearDrawing,
  exportDrawingJSON,
  importDrawingJSON,
} from '@/lib/draw-persistence';
import type { DrawingData } from '@/lib/draw-types';

/** Minimal valid DrawingData fixture for use in tests. */
const makeDrawingData = (): DrawingData => ({
  version: 1,
  canvas_width: 800,
  canvas_height: 600,
  background_color: '#FFFFFF',
  strokes: [
    {
      index: 0,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test stroke',
      type: 'line',
      color_hex: '#FF0000',
      thickness: 2,
      opacity: 1.0,
      start_x: 10,
      start_y: 20,
      end_x: 100,
      end_y: 200,
    },
    {
      index: 1,
      iteration: 1,
      batch_position: 0,
      batch_reasoning: 'second stroke',
      type: 'circle',
      color_hex: '#0000FF',
      thickness: 1,
      opacity: 0.8,
      center_x: 50,
      center_y: 50,
      radius: 25,
      fill: true,
    },
  ],
});

describe('localStorage persistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('saveDrawing / loadDrawing round-trip', () => {
    it('returns deep-equal data after save then load', () => {
      const data = makeDrawingData();
      saveDrawing(data);
      const loaded = loadDrawing();
      expect(loaded).toEqual(data);
    });
  });

  describe('loadDrawing', () => {
    it('returns null when localStorage is empty', () => {
      const result = loadDrawing();
      expect(result).toBeNull();
    });

    it('returns null when localStorage contains invalid JSON', () => {
      localStorage.setItem('pblm-draw-canvas', '{bad json}');
      const result = loadDrawing();
      expect(result).toBeNull();
    });
  });

  describe('clearDrawing', () => {
    it('causes loadDrawing to return null after clearing a saved drawing', () => {
      const data = makeDrawingData();
      saveDrawing(data);
      expect(loadDrawing()).not.toBeNull();
      clearDrawing();
      expect(loadDrawing()).toBeNull();
    });
  });
});

describe('exportDrawingJSON', () => {
  it('produces valid JSON that parses back to the original data', () => {
    const data = makeDrawingData();
    const json = exportDrawingJSON(data);
    expect(() => JSON.parse(json)).not.toThrow();
    expect(JSON.parse(json)).toEqual(data);
  });
});

describe('importDrawingJSON', () => {
  it('returns deep-equal data for valid JSON input', () => {
    const data = makeDrawingData();
    const json = JSON.stringify(data);
    const result = importDrawingJSON(json);
    expect(result).toEqual(data);
  });

  it('returns null for empty string', () => {
    expect(importDrawingJSON('')).toBeNull();
  });

  it('returns null for malformed JSON', () => {
    expect(importDrawingJSON('{bad')).toBeNull();
  });

  it('returns null when version field is missing', () => {
    const data = makeDrawingData();
    const { version: _version, ...withoutVersion } = data;
    expect(importDrawingJSON(JSON.stringify(withoutVersion))).toBeNull();
  });

  it('returns null when version is wrong (e.g. 2)', () => {
    const data = { ...makeDrawingData(), version: 2 };
    expect(importDrawingJSON(JSON.stringify(data))).toBeNull();
  });

  it('returns null when strokes field is missing', () => {
    const data = makeDrawingData();
    const { strokes: _strokes, ...withoutStrokes } = data;
    expect(importDrawingJSON(JSON.stringify(withoutStrokes))).toBeNull();
  });

  it('returns null when strokes is not an array', () => {
    const data = { ...makeDrawingData(), strokes: 'not-an-array' };
    expect(importDrawingJSON(JSON.stringify(data))).toBeNull();
  });

  it('returns null when canvas_width is zero', () => {
    const data = { ...makeDrawingData(), canvas_width: 0 };
    expect(importDrawingJSON(JSON.stringify(data))).toBeNull();
  });

  it('returns null when canvas_width is negative', () => {
    const data = { ...makeDrawingData(), canvas_width: -1 };
    expect(importDrawingJSON(JSON.stringify(data))).toBeNull();
  });

  it('returns null when canvas_height is zero', () => {
    const data = { ...makeDrawingData(), canvas_height: 0 };
    expect(importDrawingJSON(JSON.stringify(data))).toBeNull();
  });

  it('returns null when canvas_height is negative', () => {
    const data = { ...makeDrawingData(), canvas_height: -100 };
    expect(importDrawingJSON(JSON.stringify(data))).toBeNull();
  });

  it('returns null when background_color is missing', () => {
    const data = makeDrawingData();
    const { background_color: _bg, ...withoutBg } = data;
    expect(importDrawingJSON(JSON.stringify(withoutBg))).toBeNull();
  });
});
