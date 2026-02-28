/**
 * Canvas 2D rendering functions for all stroke types.
 *
 * Provides type-specific rendering for line, arc, polyline, circle, and
 * splatter strokes. Each renderer supports both visual rendering (with
 * color and opacity) and hit-detection rendering (with unique solid colors).
 */

import type { EnrichedStroke } from '@/lib/types';
import { hexToRGBA, strokeIndexToColor } from '@/lib/color-utils';
import { mulberry32 } from '@/lib/prng';

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
  }
  ctx.restore();
}

/**
 * Render a straight line stroke.
 */
function renderLine(ctx: CanvasRenderingContext2D, stroke: EnrichedStroke, isHit: boolean): void {
  const color = isHit
    ? strokeIndexToColor(stroke.index)
    : hexToRGBA(stroke.color_hex, stroke.opacity);

  ctx.beginPath();
  ctx.moveTo(stroke.start_x!, stroke.start_y!);
  ctx.lineTo(stroke.end_x!, stroke.end_y!);
  ctx.strokeStyle = color;
  ctx.lineWidth = isHit ? Math.max(stroke.thickness, 4) : stroke.thickness;
  ctx.lineCap = 'butt';
  ctx.stroke();
}

/**
 * Render an elliptical arc stroke.
 */
function renderArc(ctx: CanvasRenderingContext2D, stroke: EnrichedStroke, isHit: boolean): void {
  const [x0, y0, x1, y1] = stroke.arc_bbox!;
  const cx = (x0 + x1) / 2;
  const cy = (y0 + y1) / 2;
  const rx = (x1 - x0) / 2;
  const ry = (y1 - y0) / 2;
  const startRad = (stroke.arc_start_angle! * Math.PI) / 180;
  const endRad = (stroke.arc_end_angle! * Math.PI) / 180;
  const color = isHit
    ? strokeIndexToColor(stroke.index)
    : hexToRGBA(stroke.color_hex, stroke.opacity);

  ctx.beginPath();
  ctx.ellipse(cx, cy, Math.abs(rx), Math.abs(ry), 0, startRad, endRad, false);
  ctx.strokeStyle = color;
  ctx.lineWidth = isHit ? Math.max(stroke.thickness, 4) : stroke.thickness;
  ctx.stroke();
}

/**
 * Render a multi-segment polyline stroke.
 */
function renderPolyline(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  isHit: boolean
): void {
  if (!stroke.points || stroke.points.length < 2) return;
  const color = isHit
    ? strokeIndexToColor(stroke.index)
    : hexToRGBA(stroke.color_hex, stroke.opacity);

  ctx.beginPath();
  ctx.moveTo(stroke.points[0][0], stroke.points[0][1]);
  for (let i = 1; i < stroke.points.length; i++) {
    ctx.lineTo(stroke.points[i][0], stroke.points[i][1]);
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = isHit ? Math.max(stroke.thickness, 4) : stroke.thickness;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  ctx.stroke();
}

/**
 * Render a circle stroke (filled or outlined).
 */
function renderCircle(ctx: CanvasRenderingContext2D, stroke: EnrichedStroke, isHit: boolean): void {
  const color = isHit
    ? strokeIndexToColor(stroke.index)
    : hexToRGBA(stroke.color_hex, stroke.opacity);

  ctx.beginPath();
  ctx.arc(stroke.center_x!, stroke.center_y!, stroke.radius!, 0, Math.PI * 2);
  if (stroke.fill) {
    ctx.fillStyle = color;
    ctx.fill();
  } else {
    ctx.strokeStyle = color;
    ctx.lineWidth = isHit ? Math.max(stroke.thickness, 4) : stroke.thickness;
    ctx.stroke();
  }
}

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
function renderSplatter(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  globalIndex: number,
  isHit: boolean
): void {
  const color = isHit
    ? strokeIndexToColor(stroke.index)
    : hexToRGBA(stroke.color_hex, stroke.opacity);

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

    ctx.beginPath();
    ctx.arc(dotX, dotY, dotRadius, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }
}

/**
 * Render a dry-brush stroke with visible bristle gaps.
 *
 * Creates textured brush strokes by drawing multiple parallel bristle lines
 * with seeded-random gaps and jitter. Uses the same PRNG-based algorithm as
 * the Python backend for identical visual output.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
 * @param {EnrichedStroke} stroke - Stroke data with dry-brush parameters
 * @param {number} globalIndex - Stroke index (unused, using first point as seed)
 * @param {boolean} isHit - Hit detection mode flag
 */
function renderDryBrush(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  globalIndex: number,
  isHit: boolean
): void {
  if (!stroke.points || stroke.points.length < 2) return;

  const color = isHit
    ? strokeIndexToColor(stroke.index)
    : hexToRGBA(stroke.color_hex, stroke.opacity);

  const brushWidth = stroke.brush_width!;
  const bristleCount = stroke.bristle_count!;
  const gapProbability = stroke.gap_probability!;

  // Calculate bristle thickness (distribute total thickness across bristles)
  const bristleThickness = Math.max(1, Math.floor(stroke.thickness / bristleCount));

  // Create seed from first point coordinates for deterministic randomness
  // Use same hash as Python: hash(tuple(points[0]))
  const seed = stroke.points[0][0] * 31 + stroke.points[0][1];

  // Render each bristle
  for (let bristleIdx = 0; bristleIdx < bristleCount; bristleIdx++) {
    // Create PRNG for this bristle (same seed derivation as Python)
    const rng = mulberry32(seed + bristleIdx);

    // Calculate offset for this bristle (evenly spaced across brush_width)
    let offset = 0;
    if (bristleCount > 1) {
      offset = (bristleIdx / (bristleCount - 1) - 0.5) * brushWidth;
    }

    // Walk the polyline path segment by segment
    for (let segIdx = 0; segIdx < stroke.points.length - 1; segIdx++) {
      const p0 = stroke.points[segIdx];
      const p1 = stroke.points[segIdx + 1];

      // Compute segment direction and length
      const dx = p1[0] - p0[0];
      const dy = p1[1] - p0[1];
      const length = Math.sqrt(dx * dx + dy * dy);

      if (length < 0.001) continue; // Skip degenerate segments

      // Normalize direction vector
      const dirX = dx / length;
      const dirY = dy / length;

      // Perpendicular direction (rotated 90 degrees)
      const perpX = -dirY;
      const perpY = dirX;

      // Add small random jitter to perpendicular offset (±10% of brush_width)
      const jitter = (rng() - 0.5) * brushWidth * 0.2;
      const actualOffset = offset + jitter;

      // Calculate bristle segment endpoints
      const bristleP0X = p0[0] + perpX * actualOffset;
      const bristleP0Y = p0[1] + perpY * actualOffset;
      const bristleP1X = p1[0] + perpX * actualOffset;
      const bristleP1Y = p1[1] + perpY * actualOffset;

      // For hit detection, draw all segments solid (no gaps)
      if (!isHit) {
        // Decide whether to skip this segment (create gap)
        if (rng() < gapProbability) {
          continue; // Skip this segment
        }
      }

      // Draw this bristle segment
      ctx.beginPath();
      ctx.moveTo(bristleP0X, bristleP0Y);
      ctx.lineTo(bristleP1X, bristleP1Y);
      ctx.strokeStyle = color;
      ctx.lineWidth = isHit ? Math.max(bristleThickness, 1) : bristleThickness;
      ctx.lineCap = 'butt';
      ctx.stroke();
    }
  }
}
