/**
 * Renderer for circle strokes (filled or outlined).
 */

import type { EnrichedStroke } from '@/lib/types';
import { strokeColor, hitLineWidth } from '@/utils/renderer-utils';

/**
 * Render a circle stroke (filled or outlined).
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas 2D rendering context
 * @param {EnrichedStroke} stroke - Stroke data with circle parameters
 * @param {boolean} isHit - If true, render with unique solid color for hit detection
 */
export function renderCircle(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  isHit: boolean
): void {
  const color = strokeColor(stroke, isHit);

  ctx.beginPath();
  ctx.arc(stroke.center_x!, stroke.center_y!, stroke.radius!, 0, Math.PI * 2);
  if (stroke.fill) {
    ctx.fillStyle = color;
    ctx.fill();
  } else {
    ctx.strokeStyle = color;
    ctx.lineWidth = isHit ? hitLineWidth(stroke.thickness) : stroke.thickness;
    ctx.stroke();
  }
}
