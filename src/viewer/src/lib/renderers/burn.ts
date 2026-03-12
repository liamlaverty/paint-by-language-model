/**
 * Renderer for burn strokes that darken existing pixels in a soft circular region.
 */

import type { EnrichedStroke } from '@/lib/types';
import { drawFilledCircle } from '@/lib/renderers/renderer-utils';
import { strokeIndexToColor } from '@/lib/color-utils';

/**
 * Render a burn stroke that darkens existing pixels in a soft circular region.
 *
 * Uses {@link CanvasRenderingContext2D.globalCompositeOperation} set to
 * `'multiply'` with a radial gradient that fades from a dark centre
 * (proportional to `intensity`) to white at the edge of `radius`.
 * Under multiply blending, multiplying by white (255) leaves pixels unchanged,
 * while multiplying by a darker value darkens them.
 *
 * For hit detection, draws a solid filled circle instead.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
 * @param {EnrichedStroke} stroke - Stroke data with burn parameters
 *   (`center_x`, `center_y`, `radius`, `intensity`)
 * @param {boolean} isHit - Hit detection mode flag
 */
export function renderBurn(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  isHit: boolean
): void {
  const cx = stroke.center_x!;
  const cy = stroke.center_y!;
  const radius = stroke.radius!;
  const intensity = stroke.intensity ?? 0.5;

  if (isHit) {
    // Hit detection: solid filled circle with index colour
    drawFilledCircle(ctx, cx, cy, radius, strokeIndexToColor(stroke.index));
    return;
  }

  // Visual rendering: radial gradient multiply blend
  ctx.globalCompositeOperation = 'multiply';
  const v = Math.round(255 * (1 - intensity));
  const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
  gradient.addColorStop(0, `rgb(${v}, ${v}, ${v})`);
  gradient.addColorStop(1, 'rgb(255, 255, 255)');
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fill();
}
