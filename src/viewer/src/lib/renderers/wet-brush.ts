/**
 * Renderer for wet-brush strokes with soft, bleeding edges.
 */

import type { EnrichedStroke } from '@/lib/types';
import { strokeIndexToColor, hexToRGBA } from '@/lib/color-utils';

/**
 * Render a wet-brush stroke with soft, bleeding edges.
 *
 * For visual rendering, applies a CSS blur filter to simulate Gaussian paint
 * bleed (matching the PIL GaussianBlur used in the Python renderer). Effective
 * opacity is stroke.opacity multiplied by stroke.flow, matching the Python
 * alpha = opacity * flow * 255 formula.
 *
 * For hit detection, draws the polyline without blur using a wider line to
 * account for the blur spread.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
 * @param {EnrichedStroke} stroke - Stroke data with wet-brush parameters
 * @param {boolean} isHit - Hit detection mode flag
 */
export function renderWetBrush(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  isHit: boolean
): void {
  if (!stroke.points || stroke.points.length < 2) return;

  if (isHit) {
    // Hit detection: draw wider line without blur to account for blur spread
    const hitWidth = Math.max(stroke.thickness + (stroke.softness ?? 0) * 2, 4);
    ctx.beginPath();
    ctx.moveTo(stroke.points[0][0], stroke.points[0][1]);
    for (let i = 1; i < stroke.points.length; i++) {
      ctx.lineTo(stroke.points[i][0], stroke.points[i][1]);
    }
    ctx.strokeStyle = strokeIndexToColor(stroke.index);
    ctx.lineWidth = hitWidth;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.stroke();
  } else {
    // Visual rendering: apply blur filter and flow-adjusted alpha
    const effectiveOpacity = stroke.opacity * (stroke.flow ?? 1.0);
    ctx.filter = `blur(${stroke.softness ?? 0}px)`;
    ctx.globalAlpha = effectiveOpacity;
    ctx.beginPath();
    ctx.moveTo(stroke.points[0][0], stroke.points[0][1]);
    for (let i = 1; i < stroke.points.length; i++) {
      ctx.lineTo(stroke.points[i][0], stroke.points[i][1]);
    }
    ctx.strokeStyle = hexToRGBA(stroke.color_hex, 1.0);
    ctx.lineWidth = stroke.thickness;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.stroke();
  }
}
