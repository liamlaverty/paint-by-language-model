/**
 * Unit tests for draw-types.ts - Stroke type constants and mappings
 */

import { STROKE_TYPES, STROKE_INTERACTION, STROKE_DEFAULTS } from '@/lib/draw-types';
import type { InteractionMode } from '@/lib/draw-types';

const VALID_INTERACTION_MODES: InteractionMode[] = ['two-point', 'center-radius', 'multi-point'];

describe('STROKE_TYPES', () => {
  it('contains exactly 10 entries', () => {
    expect(STROKE_TYPES).toHaveLength(10);
  });

  it('contains all expected stroke type values', () => {
    const expected = [
      'line',
      'arc',
      'polyline',
      'circle',
      'splatter',
      'dry-brush',
      'chalk',
      'wet-brush',
      'burn',
      'dodge',
    ] as const;

    for (const type of expected) {
      expect(STROKE_TYPES).toContain(type);
    }
  });
});

describe('STROKE_INTERACTION', () => {
  it('has a key for every entry in STROKE_TYPES', () => {
    for (const type of STROKE_TYPES) {
      expect(STROKE_INTERACTION).toHaveProperty(type);
    }
  });

  it('all values are valid InteractionMode values', () => {
    for (const type of STROKE_TYPES) {
      expect(VALID_INTERACTION_MODES).toContain(STROKE_INTERACTION[type]);
    }
  });

  it('assigns line to two-point', () => {
    expect(STROKE_INTERACTION['line']).toBe('two-point');
  });

  it('assigns circle to center-radius', () => {
    expect(STROKE_INTERACTION['circle']).toBe('center-radius');
  });

  it('assigns polyline to multi-point', () => {
    expect(STROKE_INTERACTION['polyline']).toBe('multi-point');
  });
});

describe('STROKE_DEFAULTS', () => {
  it('has a key for every entry in STROKE_TYPES', () => {
    for (const type of STROKE_TYPES) {
      expect(STROKE_DEFAULTS).toHaveProperty(type);
    }
  });

  it('splatter defaults contain splatter_count, dot_size_min, dot_size_max', () => {
    const defaults = STROKE_DEFAULTS['splatter'];
    expect(defaults).toHaveProperty('splatter_count');
    expect(defaults).toHaveProperty('dot_size_min');
    expect(defaults).toHaveProperty('dot_size_max');
  });

  it('dry-brush defaults contain brush_width, bristle_count, gap_probability', () => {
    const defaults = STROKE_DEFAULTS['dry-brush'];
    expect(defaults).toHaveProperty('brush_width');
    expect(defaults).toHaveProperty('bristle_count');
    expect(defaults).toHaveProperty('gap_probability');
  });

  it('chalk defaults contain chalk_width, grain_density', () => {
    const defaults = STROKE_DEFAULTS['chalk'];
    expect(defaults).toHaveProperty('chalk_width');
    expect(defaults).toHaveProperty('grain_density');
  });

  it('wet-brush defaults contain softness, flow', () => {
    const defaults = STROKE_DEFAULTS['wet-brush'];
    expect(defaults).toHaveProperty('softness');
    expect(defaults).toHaveProperty('flow');
  });

  it('burn defaults contain intensity', () => {
    const defaults = STROKE_DEFAULTS['burn'];
    expect(defaults).toHaveProperty('intensity');
  });

  it('dodge defaults contain intensity', () => {
    const defaults = STROKE_DEFAULTS['dodge'];
    expect(defaults).toHaveProperty('intensity');
  });
});
