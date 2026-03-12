/**
 * Renderer for elliptical arc strokes.
 */

import type { EnrichedStroke } from '@/lib/types';
import { hitLineWidth, strokeColor } from '@/utils/renderer-utils';

/**
 * Render an elliptical arc stroke.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas 2D rendering context
 * @param {EnrichedStroke} stroke - Stroke data with arc parameters
 * @param {boolean} isHit - If true, render with unique solid color for hit detection
 */
export function renderArc(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  isHit: boolean
): void {
  const [x0, y0, x1, y1] = stroke.arc_bbox!;
  const cx = (x0 + x1) / 2;
  const cy = (y0 + y1) / 2;
  const rx = (x1 - x0) / 2;
  const ry = (y1 - y0) / 2;
  const startRad = (stroke.arc_start_angle! * Math.PI) / 180;
  const endRad = (stroke.arc_end_angle! * Math.PI) / 180;
  const color = strokeColor(stroke, isHit);

  ctx.beginPath();
  ctx.ellipse(cx, cy, Math.abs(rx), Math.abs(ry), 0, startRad, endRad, false);
  ctx.strokeStyle = color;
  ctx.lineWidth = isHit ? hitLineWidth(stroke.thickness) : stroke.thickness;
  ctx.stroke();
}
