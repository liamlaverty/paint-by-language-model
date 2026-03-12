/**
 * Renderer for multi-segment polyline strokes.
 */

import type { EnrichedStroke } from '@/lib/types';
import { strokeColor, hitLineWidth } from '@/lib/renderers/renderer-utils';

/**
 * Render a multi-segment polyline stroke.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas 2D rendering context
 * @param {EnrichedStroke} stroke - Stroke data with points array
 * @param {boolean} isHit - If true, render with unique solid color for hit detection
 */
export function renderPolyline(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  isHit: boolean
): void {
  if (!stroke.points || stroke.points.length < 2) return;
  const color = strokeColor(stroke, isHit);

  ctx.beginPath();
  ctx.moveTo(stroke.points[0][0], stroke.points[0][1]);
  for (let i = 1; i < stroke.points.length; i++) {
    ctx.lineTo(stroke.points[i][0], stroke.points[i][1]);
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = isHit ? hitLineWidth(stroke.thickness) : stroke.thickness;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  ctx.stroke();
}
