/**
 * Shared utilities for canvas stroke renderers.
 *
 * Provides helpers that are used across multiple renderer implementations to
 * avoid duplication of common canvas drawing patterns.
 */

import type { EnrichedStroke } from '@/lib/types';
import { hexToRGBA, strokeIndexToColor } from '@/lib/color-utils';

/**
 * Resolve the CSS color string to use for a stroke.
 *
 * Returns the hit-detection index colour when `isHit` is true, otherwise
 * returns the stroke's actual hex color with opacity applied.
 *
 * @param {EnrichedStroke} stroke - Stroke data containing color and index fields
 * @param {boolean} isHit - Whether to render in hit-detection mode
 * @returns {string} CSS color string
 */
export function strokeColor(stroke: EnrichedStroke, isHit: boolean): string {
  return isHit
    ? strokeIndexToColor(stroke.index)
    : hexToRGBA(stroke.color_hex, stroke.opacity);
}

/**
 * Return the effective line width for hit-detection rendering.
 *
 * Ensures a minimum width of 4px so thin strokes remain clickable.
 *
 * @param {number} thickness - The stroke's nominal thickness
 * @returns {number} Line width to use for hit-detection rendering
 */
export function hitLineWidth(thickness: number): number {
  return Math.max(thickness, 4);
}

/**
 * Draw a filled circle on the canvas.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
 * @param {number} cx - Circle centre x coordinate
 * @param {number} cy - Circle centre y coordinate
 * @param {number} radius - Circle radius
 * @param {string} color - CSS fill color string
 */
export function drawFilledCircle(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  color: string
): void {
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
}
