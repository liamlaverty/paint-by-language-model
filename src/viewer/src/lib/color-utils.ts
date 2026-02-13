/**
 * Color conversion and encoding utilities for canvas rendering.
 *
 * Provides functions for converting between hex colors and RGBA strings,
 * as well as encoding/decoding stroke indices as RGB colors for hit detection.
 */

/**
 * Convert a hexadecimal color string to an RGBA CSS string.
 *
 * Handles both 6-digit (#RRGGBB) and 8-digit (#RRGGBBAA) hex formats.
 * For 6-digit hex, uses the provided opacity parameter. For 8-digit hex,
 * extracts the alpha channel from the hex string.
 *
 * @param {string} hex - Hex color string (with or without leading #)
 * @param {number} opacity - Opacity value (0.0 to 1.0), used for 6-digit hex
 * @returns {string} CSS rgba() color string
 *
 * @example
 * hexToRGBA('#FF5733', 0.5)     // 'rgba(255,87,51,0.5)'
 * hexToRGBA('#FF5733CC', 1.0)   // 'rgba(255,87,51,0.8)'
 */
export function hexToRGBA(hex: string, opacity: number): string {
  const h = hex.replace('#', '');
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  if (h.length === 8) {
    const a = parseInt(h.substring(6, 8), 16) / 255;
    return `rgba(${r},${g},${b},${a})`;
  }
  return `rgba(${r},${g},${b},${opacity})`;
}

/**
 * Encode a stroke index as a unique RGB color for hit-canvas rendering.
 *
 * Maps stroke indices to unique RGB colors for pixel-perfect hit detection.
 * Index 0 maps to rgb(0,0,1), reserving rgb(0,0,0) for background.
 * Supports indices from 0 to 16,777,214 (2^24 - 2).
 *
 * @param {number} index - Stroke index (0-based)
 * @returns {string} CSS rgb() color string
 *
 * @example
 * strokeIndexToColor(0)     // 'rgb(0,0,1)'
 * strokeIndexToColor(255)   // 'rgb(0,1,0)'
 * strokeIndexToColor(65535) // 'rgb(0,255,255)'
 */
export function strokeIndexToColor(index: number): string {
  const id = index + 1;
  const r = (id >> 16) & 0xff;
  const g = (id >> 8) & 0xff;
  const b = id & 0xff;
  return `rgb(${r},${g},${b})`;
}

/**
 * Decode an RGB color pixel back to a stroke index.
 *
 * Inverse of strokeIndexToColor(). Returns -1 for background pixels (0,0,0).
 *
 * @param {number} r - Red channel value (0-255)
 * @param {number} g - Green channel value (0-255)
 * @param {number} b - Blue channel value (0-255)
 * @returns {number} Stroke index (0-based), or -1 for background
 *
 * @example
 * colorToStrokeIndex(0, 0, 1)     // 0
 * colorToStrokeIndex(0, 1, 0)     // 255
 * colorToStrokeIndex(0, 0, 0)     // -1 (background)
 */
export function colorToStrokeIndex(r: number, g: number, b: number): number {
  if (r === 0 && g === 0 && b === 0) return -1;
  return ((r << 16) | (g << 8) | b) - 1;
}
