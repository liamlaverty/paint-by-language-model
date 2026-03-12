/**
 * Renderer for straight line strokes.
 */

import type { EnrichedStroke } from '@/lib/types';
import { strokeColor, hitLineWidth } from '@/lib/renderers/renderer-utils';

/**
 * Render a straight line stroke.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas 2D rendering context
 * @param {EnrichedStroke} stroke - Stroke data with rendering parameters
 * @param {boolean} isHit - If true, render with unique solid color for hit detection
 */
export function renderLine(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  isHit: boolean
): void {
  const color = strokeColor(stroke, isHit);

  ctx.beginPath();
  ctx.moveTo(stroke.start_x!, stroke.start_y!);
  ctx.lineTo(stroke.end_x!, stroke.end_y!);
  ctx.strokeStyle = color;
  ctx.lineWidth = isHit ? hitLineWidth(stroke.thickness) : stroke.thickness;
  ctx.lineCap = 'butt';
  ctx.stroke();
}
