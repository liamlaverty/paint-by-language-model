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
    case 'chalk':
      renderChalk(ctx, stroke, index, isHit);
      break;
    case 'wet-brush':
      renderWetBrush(ctx, stroke, isHit);
      break;
    case 'burn':
      renderBurn(ctx, stroke, isHit);
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
function renderBurn(ctx: CanvasRenderingContext2D, stroke: EnrichedStroke, isHit: boolean): void {
  const cx = stroke.center_x!;
  const cy = stroke.center_y!;
  const radius = stroke.radius!;
  const intensity = stroke.intensity ?? 0.5;

  if (isHit) {
    // Hit detection: solid filled circle with index colour
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = strokeIndexToColor(stroke.index);
    ctx.fill();
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

function renderWetBrush(
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

/**
 * Render a chalk stroke with grainy texture.
 *
 * Creates grainy, textured strokes along a polyline path by generating many
 * small random dots clustered within a perpendicular band. Mimics chalk or
 * pastel on rough paper. Uses seeded PRNG for deterministic dot placement.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
 * @param {EnrichedStroke} stroke - Stroke data with chalk parameters
 * @param {number} globalIndex - Stroke index (unused, using sample point as seed)
 * @param {boolean} isHit - Hit detection mode flag
 */
function renderChalk(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  globalIndex: number,
  isHit: boolean
): void {
  if (!stroke.points || stroke.points.length < 2) return;

  const color = isHit
    ? strokeIndexToColor(stroke.index)
    : hexToRGBA(stroke.color_hex, stroke.opacity);

  const chalkWidth = stroke.chalk_width!;
  const grainDensity = stroke.grain_density!;

  // Get canvas dimensions
  const canvasW = ctx.canvas.width || 800;
  const canvasH = ctx.canvas.height || 600;

  // Walk the polyline path and generate sample points
  const sampleSpacing = 2.0; // pixels between sample points

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

    // Generate evenly-spaced sample points along this segment
    const numSamples = Math.max(1, Math.floor(length / sampleSpacing));

    for (let sampleIdx = 0; sampleIdx < numSamples; sampleIdx++) {
      // Calculate position along segment
      const t = numSamples > 1 ? sampleIdx / (numSamples - 1) : 0.5;
      const sampleX = p0[0] + t * dx;
      const sampleY = p0[1] + t * dy;

      // Create seed from sample point coordinates for deterministic randomness
      // Match Python: hash((seg_idx, sample_idx, int(sample_x), int(sample_y)))
      const seed =
        segIdx * 1000000 + sampleIdx * 1000 + Math.floor(sampleX) * 31 + Math.floor(sampleY);

      // For hit detection, draw solid polyline band instead of grainy dots
      if (isHit) {
        // Draw a filled band for reliable hit detection
        // Simply draw the path thick enough to cover the chalk_width
        ctx.beginPath();
        ctx.moveTo(sampleX, sampleY);
        const nextT = numSamples > 1 ? (sampleIdx + 1) / (numSamples - 1) : 1.0;
        const nextX = p0[0] + nextT * dx;
        const nextY = p0[1] + nextT * dy;
        ctx.lineTo(nextX, nextY);
        ctx.strokeStyle = color;
        ctx.lineWidth = chalkWidth;
        ctx.lineCap = 'round';
        ctx.stroke();
      } else {
        // Generate grain_density random dots at this sample point
        const rng = mulberry32(seed);

        for (let dotIdx = 0; dotIdx < grainDensity; dotIdx++) {
          // Random perpendicular offset within ±chalk_width/2
          const perpOffset = (rng() - 0.5) * chalkWidth;

          // Random radius between 1 and 3 pixels
          const dotRadius = 1 + rng() * 2;

          // Calculate dot position
          const dotX = sampleX + perpX * perpOffset;
          const dotY = sampleY + perpY * perpOffset;

          // Skip dots that fall entirely outside canvas bounds
          if (
            dotX + dotRadius < 0 ||
            dotY + dotRadius < 0 ||
            dotX - dotRadius >= canvasW ||
            dotY - dotRadius >= canvasH
          ) {
            continue;
          }

          // Draw dot as small circle
          ctx.beginPath();
          ctx.arc(dotX, dotY, dotRadius, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();
        }
      }
    }
  }
}
