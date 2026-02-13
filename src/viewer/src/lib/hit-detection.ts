/**
 * Hit detection utilities for mapping mouse positions to stroke indices.
 *
 * Provides functions to determine which stroke is under the mouse cursor
 * by reading pixel colors from a hidden hit-detection canvas.
 */

import { colorToStrokeIndex } from '@/lib/color-utils';

/**
 * Get the stroke index at a given mouse position.
 *
 * Reads a pixel from the hit-detection canvas at the specified client
 * coordinates, accounting for CSS scaling vs canvas resolution. Returns
 * the stroke index encoded in the pixel color, or -1 if the mouse is
 * over the background.
 *
 * @param {CanvasRenderingContext2D} hitCtx - Hit-detection canvas context
 *   (must be rendered with strokeIndexToColor for each stroke)
 * @param {HTMLCanvasElement} canvasEl - The canvas element (for coordinate scaling)
 * @param {number} clientX - Mouse X position in client coordinates
 * @param {number} clientY - Mouse Y position in client coordinates
 * @returns {number} Stroke index (0-based), or -1 if no stroke at this position
 *
 * @example
 * function handleMouseMove(event) {
 *   const rect = mainCanvas.getBoundingClientRect();
 *   const index = getStrokeIndexAtPoint(
 *     hitCtx,
 *     mainCanvas,
 *     event.clientX - rect.left,
 *     event.clientY - rect.top
 *   );
 *   if (index >= 0) {
 *     highlightStroke(index);
 *   }
 * }
 */
export function getStrokeIndexAtPoint(
  hitCtx: CanvasRenderingContext2D,
  canvasEl: HTMLCanvasElement,
  clientX: number,
  clientY: number
): number {
  // Account for CSS scaling vs canvas resolution
  const rect = canvasEl.getBoundingClientRect();
  const scaleX = canvasEl.width / rect.width;
  const scaleY = canvasEl.height / rect.height;

  const canvasX = Math.floor(clientX * scaleX);
  const canvasY = Math.floor(clientY * scaleY);

  // Validate coordinates are within canvas bounds
  if (canvasX < 0 || canvasY < 0 || canvasX >= canvasEl.width || canvasY >= canvasEl.height) {
    return -1; // Out of bounds = background
  }

  // Read pixel color from hit canvas
  const pixel = hitCtx.getImageData(canvasX, canvasY, 1, 1).data;
  const r = pixel[0];
  const g = pixel[1];
  const b = pixel[2];

  return colorToStrokeIndex(r, g, b);
}
