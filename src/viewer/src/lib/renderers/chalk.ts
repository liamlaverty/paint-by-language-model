/**
 * Renderer for chalk strokes with grainy texture.
 */

import type { EnrichedStroke } from '@/lib/types';
import { strokeColor, drawFilledCircle } from '@/lib/renderers/renderer-utils';
import { mulberry32 } from '@/lib/prng';

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
export function renderChalk(
  ctx: CanvasRenderingContext2D,
  stroke: EnrichedStroke,
  globalIndex: number,
  isHit: boolean
): void {
  if (!stroke.points || stroke.points.length < 2) return;

  const color = strokeColor(stroke, isHit);

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

          drawFilledCircle(ctx, dotX, dotY, dotRadius, color);
        }
      }
    }
  }
}
