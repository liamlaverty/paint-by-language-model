/**
 * localStorage persistence helpers for the interactive draw page.
 *
 * All functions are safe under SSR: they check for the `window` global before
 * accessing `localStorage`, and every read operation is wrapped in try/catch so
 * a corrupt or missing entry never throws to the caller.
 */

import type { DrawingData } from '@/lib/draw-types';

/** Key used to store the active drawing in localStorage. */
const STORAGE_KEY = 'pblm-draw-canvas';

/**
 * Serialise `data` to JSON and write it to localStorage under `STORAGE_KEY`.
 *
 * @param {DrawingData} data - The drawing to persist
 */
export function saveDrawing(data: DrawingData): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

/**
 * Read the drawing stored in localStorage, parse and validate it, and return
 * the result. Returns `null` if no drawing is stored, the stored value cannot
 * be parsed, or the stored value fails basic structural validation.
 *
 * @returns {DrawingData | null} The stored drawing, or null if unavailable
 */
export function loadDrawing(): DrawingData | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) return null;
    const parsed: unknown = JSON.parse(raw);
    return validateDrawingData(parsed);
  } catch {
    return null;
  }
}

/**
 * Remove the stored drawing from localStorage.
 */
export function clearDrawing(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
}

/**
 * Serialise `data` to a pretty-printed JSON string suitable for file download.
 *
 * @param {DrawingData} data - The drawing to export
 * @returns {string} Pretty-printed JSON representation
 */
export function exportDrawingJSON(data: DrawingData): string {
  return JSON.stringify(data, null, 2);
}

/**
 * Parse `json` and validate it as a `DrawingData` object.
 *
 * Validation rules:
 * - `version` must equal `1`
 * - `strokes` must be an array
 * - `canvas_width` and `canvas_height` must be positive numbers
 * - `background_color` must be a non-empty string
 *
 * @param {string} json - Raw JSON string to import
 * @returns {DrawingData | null} Parsed drawing if valid, otherwise null
 */
export function importDrawingJSON(json: string): DrawingData | null {
  try {
    const parsed: unknown = JSON.parse(json);
    return validateDrawingData(parsed);
  } catch {
    return null;
  }
}

/**
 * Validate that `value` conforms to the `DrawingData` schema.
 *
 * @param {unknown} value - The value to validate
 * @returns {DrawingData | null} The value cast to DrawingData if valid, otherwise null
 */
function validateDrawingData(value: unknown): DrawingData | null {
  if (typeof value !== 'object' || value === null) return null;
  const candidate = value as Record<string, unknown>;

  if (candidate['version'] !== 1) return null;
  if (!Array.isArray(candidate['strokes'])) return null;
  if (typeof candidate['canvas_width'] !== 'number' || candidate['canvas_width'] <= 0) return null;
  if (typeof candidate['canvas_height'] !== 'number' || candidate['canvas_height'] <= 0)
    return null;
  if (
    typeof candidate['background_color'] !== 'string' ||
    candidate['background_color'].length === 0
  )
    return null;

  return candidate as unknown as DrawingData;
}
