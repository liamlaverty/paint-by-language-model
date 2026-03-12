/**
 * Renderer for dry-brush strokes with visible bristle gaps.
 */

import type { EnrichedStroke } from '@/lib/types';
import { strokeColor } from '@/lib/renderers/renderer-utils';
import { mulberry32 } from '@/lib/prng';

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
export function renderDryBrush(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  globalIndex: number,
  isHit: boolean
): void {
  if (!stroke.points || stroke.points.length < 2) return;

  const color = strokeColor(stroke, isHit);

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
