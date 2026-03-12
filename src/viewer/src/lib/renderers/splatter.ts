/**
 * Renderer for splatter strokes (random dots).
 */

import type { EnrichedStroke } from '@/lib/types';
import { strokeColor, drawFilledCircle } from '@/utils/renderer-utils';
import { mulberry32 } from '@/lib/prng';

/**
 * Render a splatter stroke (random dots).
 *
 * Uses seeded PRNG for deterministic dot placement. Skips dots that fall
 * entirely outside canvas bounds.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
 * @param {EnrichedStroke} stroke - Stroke data with splatter parameters
 * @param {number} globalIndex - Stroke index used as PRNG seed
 * @param {boolean} isHit - Hit detection mode flag
 */
export function renderSplatter(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  globalIndex: number,
  isHit: boolean
): void {
  const color = strokeColor(stroke, isHit);

  // Use stroke index as seed for deterministic splatter
  const rng = mulberry32(globalIndex * 2654435761); // hash-like seed

  // Get canvas dimensions (fallback to reasonable defaults if not set)
  const canvasW = ctx.canvas.width || 800;
  const canvasH = ctx.canvas.height || 600;

  for (let i = 0; i < stroke.splatter_count!; i++) {
    const angle = rng() * Math.PI * 2;
    const distance = rng() * stroke.splatter_radius!;
    const dotX = stroke.center_x! + distance * Math.cos(angle);
    const dotY = stroke.center_y! + distance * Math.sin(angle);
    const dotRadius =
      Math.floor(rng() * (stroke.dot_size_max! - stroke.dot_size_min! + 1)) + stroke.dot_size_min!;

    // Skip dots entirely outside canvas (matches PIL behavior)
    if (
      dotX + dotRadius < 0 ||
      dotY + dotRadius < 0 ||
      dotX - dotRadius >= canvasW ||
      dotY - dotRadius >= canvasH
    ) {
      continue;
    }

    drawFilledCircle(ctx, dotX, dotY, dotRadius, color);
  }
}
