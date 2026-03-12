/**
 * Stroke renderer index.
 *
 * Exports the top-level `renderStroke` dispatcher and all individual renderer
 * functions. Import from this module to access any renderer directly.
 */

import type { EnrichedStroke } from '@/lib/types';
import { renderLine } from '@/lib/renderers/line';
import { renderArc } from '@/lib/renderers/arc';
import { renderPolyline } from '@/lib/renderers/polyline';
import { renderCircle } from '@/lib/renderers/circle';
import { renderSplatter } from '@/lib/renderers/splatter';
import { renderDryBrush } from '@/lib/renderers/dry-brush';
import { renderChalk } from '@/lib/renderers/chalk';
import { renderWetBrush } from '@/lib/renderers/wet-brush';
import { renderBurn } from '@/lib/renderers/burn';
import { renderDodge } from '@/lib/renderers/dodge';

export { renderLine } from '@/lib/renderers/line';
export { renderArc } from '@/lib/renderers/arc';
export { renderPolyline } from '@/lib/renderers/polyline';
export { renderCircle } from '@/lib/renderers/circle';
export { renderSplatter } from '@/lib/renderers/splatter';
export { renderDryBrush } from '@/lib/renderers/dry-brush';
export { renderChalk } from '@/lib/renderers/chalk';
export { renderWetBrush } from '@/lib/renderers/wet-brush';
export { renderBurn } from '@/lib/renderers/burn';
export { renderDodge } from '@/lib/renderers/dodge';

/**
 * Render a stroke to a canvas context.
 *
 * Delegates to type-specific renderers based on stroke.type. Wraps rendering
 * in ctx.save()/ctx.restore() to isolate canvas state changes.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas 2D rendering context
 * @param {EnrichedStroke} stroke - Stroke data with rendering parameters
 * @param {number} index - Global stroke index (used as PRNG seed for splatter)
 * @param {boolean} isHit - If true, render with unique solid color for hit detection.
 *   If false, render with actual appearance (color, opacity).
 *
 * @example
 * renderStroke(mainCtx, stroke, 0, false);  // Visual render
 * renderStroke(hitCtx, stroke, 0, true);    // Hit detection render
 */
export function renderStroke(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  index: number,
  isHit: boolean
): void {
  ctx.save();
  switch (stroke.type) {
    case 'line':
      renderLine(ctx, stroke, isHit);
      break;
    case 'arc':
      renderArc(ctx, stroke, isHit);
      break;
    case 'polyline':
      renderPolyline(ctx, stroke, isHit);
      break;
    case 'circle':
      renderCircle(ctx, stroke, isHit);
      break;
    case 'splatter':
      renderSplatter(ctx, stroke, index, isHit);
      break;
    case 'dry-brush':
      renderDryBrush(ctx, stroke, index, isHit);
      break;
    case 'chalk':
      renderChalk(ctx, stroke, index, isHit);
      break;
    case 'wet-brush':
      renderWetBrush(ctx, stroke, isHit);
      break;
    case 'burn':
      renderBurn(ctx, stroke, isHit);
      break;
    case 'dodge':
      renderDodge(ctx, stroke, isHit);
      break;
  }
  ctx.restore();
}
