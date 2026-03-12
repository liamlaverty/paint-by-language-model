/**
 * Renderer for dodge strokes that lighten existing pixels in a soft circular region.
 */

import type { EnrichedStroke } from '@/lib/types';
import { strokeIndexToColor } from '@/lib/color-utils';
import { drawFilledCircle } from '@/utils/renderer-utils';

/**
 * Render a dodge stroke that lightens existing pixels in a soft circular region.
 *
 * Uses {@link CanvasRenderingContext2D.globalCompositeOperation} set to
 * `'screen'` with a radial gradient that fades from a bright centre
 * (proportional to `intensity`) to black at the edge of `radius`.
 * Under screen blending, a black value (0) leaves pixels unchanged, while a
 * brighter value lifts the pixel towards white.
 *
 * For hit detection, draws a solid filled circle instead.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
 * @param {EnrichedStroke} stroke - Stroke data with dodge parameters
 *   (`center_x`, `center_y`, `radius`, `intensity`)
 * @param {boolean} isHit - Hit detection mode flag
 */
export function renderDodge(
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

  // Visual rendering: radial gradient screen blend
  ctx.globalCompositeOperation = 'screen';
  const v = Math.round(255 * intensity); // bright at centre
  const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
  gradient.addColorStop(0, `rgb(${v}, ${v}, ${v})`);
  gradient.addColorStop(1, 'rgb(0, 0, 0)'); // black = no effect under screen
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fill();
}
