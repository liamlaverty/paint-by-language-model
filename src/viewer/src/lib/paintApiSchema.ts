/**
 * PAINT_API_SCHEMA — single source of truth for all window.paintByLanguageModel API methods.
 *
 * Used both at runtime by usePaintWindowApi and at build time by the /draw/api documentation page.
 */

/**
 * Documentation entry for a single API method.
 *
 * @property {string} signature - TypeScript-style function signature
 * @property {string} description - Human-readable description of what the method does
 * @property {{ name: string; type: string; description: string }[]} params - Parameter list
 * @property {string} [returns] - Return value description (omit for void methods)
 * @property {string} example - Short JS snippet showing usage in the browser console
 */
export interface ApiMethodDoc {
  signature: string;
  description: string;
  params: { name: string; type: string; description: string }[];
  returns?: string;
  example: string;
}

/**
 * Complete documentation schema for the window.paintByLanguageModel API.
 *
 * All 17 methods are listed here. This constant is the authoritative source
 * consulted by both the runtime hook and the static documentation page.
 */
export const PAINT_API_SCHEMA: Record<string, ApiMethodDoc> = {
  // ── Tool / Stroke Configuration ────────────────────────────────────────────

  selectStrokeType: {
    signature: 'selectStrokeType(type: string): void',
    description:
      'Set the active stroke type. Changes take effect immediately and are reflected in the toolbar UI.',
    params: [
      {
        name: 'type',
        type: 'string',
        description:
          'One of: "line", "arc", "polyline", "circle", "splatter", "dry-brush", "chalk", "wet-brush", "burn", "dodge"',
      },
    ],
    example: 'window.paintByLanguageModel.selectStrokeType("circle");',
  },

  setColor: {
    signature: 'setColor(hex: string): void',
    description: 'Set the stroke colour. Accepts any CSS hex colour string.',
    params: [
      {
        name: 'hex',
        type: 'string',
        description: 'Hex colour string, e.g. "#ff6600" or "#3a7bd5"',
      },
    ],
    example: 'window.paintByLanguageModel.setColor("#ff6600");',
  },

  setOpacity: {
    signature: 'setOpacity(value: number): void',
    description: 'Set the stroke opacity. Changes take effect for the next committed stroke.',
    params: [
      {
        name: 'value',
        type: 'number',
        description: 'Opacity between 0.0 (transparent) and 1.0 (fully opaque)',
      },
    ],
    example: 'window.paintByLanguageModel.setOpacity(0.5);',
  },

  setThickness: {
    signature: 'setThickness(px: number): void',
    description: 'Set the stroke thickness in canvas pixels.',
    params: [
      {
        name: 'px',
        type: 'number',
        description: 'Stroke thickness in pixels (1–50)',
      },
    ],
    example: 'window.paintByLanguageModel.setThickness(8);',
  },

  setTypeParam: {
    signature: 'setTypeParam(key: string, value: unknown): void',
    description:
      'Override a type-specific parameter for the current stroke type. Use getTypeParamSchema(type) to discover available keys.',
    params: [
      {
        name: 'key',
        type: 'string',
        description:
          'Parameter key, e.g. "arc_start_angle", "fill", "splatter_count", "brush_width", "bristle_count", "gap_probability", "chalk_width", "grain_density", "softness", "flow", "intensity", "dot_size_min", "dot_size_max"',
      },
      {
        name: 'value',
        type: 'unknown',
        description: 'Value to set for the parameter',
      },
    ],
    example: 'window.paintByLanguageModel.setTypeParam("fill", true);',
  },

  // ── Canvas Interactions ────────────────────────────────────────────────────

  click: {
    signature: 'click(x: number, y: number): void',
    description:
      'Simulate a canvas click at logical pixel coordinates (x, y). For two-point and center-radius strokes this places the first or second point; for multi-point strokes it appends a point.',
    params: [
      { name: 'x', type: 'number', description: 'X coordinate in canvas pixels' },
      { name: 'y', type: 'number', description: 'Y coordinate in canvas pixels' },
    ],
    example: 'window.paintByLanguageModel.click(100, 150);',
  },

  doubleClick: {
    signature: 'doubleClick(x: number, y: number): void',
    description:
      'Simulate a canvas double-click at (x, y). Commits multi-point strokes (polyline, dry-brush, chalk, wet-brush).',
    params: [
      { name: 'x', type: 'number', description: 'X coordinate in canvas pixels' },
      { name: 'y', type: 'number', description: 'Y coordinate in canvas pixels' },
    ],
    example: 'window.paintByLanguageModel.doubleClick(200, 200);',
  },

  cancelStroke: {
    signature: 'cancelStroke(): void',
    description:
      'Discard any in-progress (uncommitted) stroke without committing it. Clears the overlay preview.',
    params: [],
    example: 'window.paintByLanguageModel.cancelStroke();',
  },

  // ── Canvas Management ──────────────────────────────────────────────────────

  clearCanvas: {
    signature: 'clearCanvas(): void',
    description:
      'Clear all committed strokes from the canvas. Does not show a confirmation dialog (unlike the toolbar Clear button).',
    params: [],
    example: 'window.paintByLanguageModel.clearCanvas();',
  },

  getStrokes: {
    signature: 'getStrokes(): object[]',
    description:
      'Return a deep copy of the current committed stroke array as plain JSON-serialisable objects.',
    params: [],
    returns: 'Array of EnrichedStroke objects (plain JSON)',
    example: 'const strokes = window.paintByLanguageModel.getStrokes();',
  },

  loadStrokes: {
    signature: 'loadStrokes(drawingJson: string): void',
    description:
      'Load a drawing from a JSON string (same format as the Download JSON feature). Replaces the current canvas content.',
    params: [
      {
        name: 'drawingJson',
        type: 'string',
        description: 'JSON string in DrawingData format (exported by downloadJSON)',
      },
    ],
    example: 'window.paintByLanguageModel.loadStrokes(JSON.stringify(drawingData));',
  },

  downloadJSON: {
    signature: 'downloadJSON(): void',
    description:
      'Programmatically trigger a browser file-download of the current drawing as a .json file.',
    params: [],
    example: 'window.paintByLanguageModel.downloadJSON();',
  },

  downloadJPG: {
    signature: 'downloadJPG(): void',
    description:
      'Programmatically trigger a browser file-download of the current canvas as a .jpg file.',
    params: [],
    example: 'window.paintByLanguageModel.downloadJPG();',
  },

  getCanvasImageDataUrl: {
    signature: 'getCanvasImageDataUrl(): string',
    description:
      'Return the current canvas as a base-64 data:image/png;base64,... string. Useful for passing to another LLM for evaluation.',
    params: [],
    returns: 'Base-64 encoded PNG data URL string',
    example: 'const dataUrl = window.paintByLanguageModel.getCanvasImageDataUrl();',
  },

  // ── Introspection ──────────────────────────────────────────────────────────

  getState: {
    signature: 'getState(): object',
    description:
      'Return a snapshot of the current tool state: activeType, color, opacity, thickness, typeParams, and strokeCount.',
    params: [],
    returns:
      '{ activeType: string, color: string, opacity: number, thickness: number, typeParams: object, strokeCount: number }',
    example: 'const state = window.paintByLanguageModel.getState();',
  },

  getStrokeTypes: {
    signature: 'getStrokeTypes(): string[]',
    description: 'Return the list of all valid stroke type names.',
    params: [],
    returns: 'Array of stroke type name strings',
    example: 'const types = window.paintByLanguageModel.getStrokeTypes();',
  },

  getTypeParamSchema: {
    signature: 'getTypeParamSchema(type: string): object',
    description:
      'Return the parameter schema and defaults for a given stroke type. Enables discovery of what setTypeParam keys are valid.',
    params: [
      {
        name: 'type',
        type: 'string',
        description: 'A valid stroke type name (see getStrokeTypes())',
      },
    ],
    returns: 'Record of parameter key → default value for the given stroke type',
    example: 'const schema = window.paintByLanguageModel.getTypeParamSchema("splatter");',
  },
};
