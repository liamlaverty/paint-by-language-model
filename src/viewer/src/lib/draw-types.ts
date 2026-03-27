/**
 * Type definitions, constants, and per-stroke defaults for the interactive draw page.
 *
 * Provides the foundational types used by DrawPage, DrawCanvas, and DrawToolbar
 * components, as well as the persistence helpers in draw-persistence.ts.
 */

import type { EnrichedStroke } from '@/lib/types';

/**
 * Portable JSON representation of a user drawing.
 *
 * Serialised to localStorage and downloadable as a JSON file.
 * The `version` field is a literal type so importDrawingJSON can
 * narrow the schema version at runtime.
 *
 * @property {1} version - Schema version (always 1 for this release)
 * @property {number} canvas_width - Canvas pixel width
 * @property {number} canvas_height - Canvas pixel height
 * @property {string} background_color - Background colour as a hex string (e.g. "#FFFFFF")
 * @property {EnrichedStroke[]} strokes - Ordered array of strokes applied to the canvas
 */
export interface DrawingData {
  version: 1;
  canvas_width: number;
  canvas_height: number;
  background_color: string;
  strokes: EnrichedStroke[];
}

/**
 * All stroke types supported by the draw page, in display order.
 *
 * Matches the `type` union in `EnrichedStroke` exactly.
 */
export const STROKE_TYPES = [
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

/**
 * A single stroke type identifier drawn from the `STROKE_TYPES` tuple.
 */
export type DrawStrokeType = (typeof STROKE_TYPES)[number];

/**
 * Canvas interaction pattern required to define a stroke.
 *
 * - `two-point`: user clicks a start point then an end point
 * - `center-radius`: user clicks a centre then a point on the edge
 * - `multi-point`: user clicks multiple points and double-clicks to finish
 */
export type InteractionMode = 'two-point' | 'center-radius' | 'multi-point';

/**
 * Maps each stroke type to the canvas interaction mode it requires.
 */
export const STROKE_INTERACTION: Record<DrawStrokeType, InteractionMode> = {
  line: 'two-point',
  arc: 'two-point',
  polyline: 'multi-point',
  circle: 'center-radius',
  splatter: 'center-radius',
  'dry-brush': 'multi-point',
  chalk: 'multi-point',
  'wet-brush': 'multi-point',
  burn: 'center-radius',
  dodge: 'center-radius',
};

/**
 * Sensible default values for the optional, type-specific parameters of each stroke type.
 *
 * These are merged into a new stroke when the user confirms a draw gesture, so that
 * each stroke has reasonable values without requiring the user to configure every field.
 */
export const STROKE_DEFAULTS: Record<DrawStrokeType, Partial<EnrichedStroke>> = {
  line: {},
  arc: {},
  polyline: {},
  circle: { fill: true },
  splatter: { splatter_count: 30, dot_size_min: 1, dot_size_max: 4 },
  'dry-brush': { brush_width: 20, bristle_count: 8, gap_probability: 0.3 },
  chalk: { chalk_width: 12, grain_density: 40 },
  'wet-brush': { softness: 3, flow: 0.8 },
  burn: { intensity: 0.3 },
  dodge: { intensity: 0.3 },
};
