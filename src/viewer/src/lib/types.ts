/**
 * TypeScript type definitions for viewer data model.
 *
 * Defines interfaces matching the viewer_data.json schema produced by
 * the Python generation orchestrator.
 */

/**
 * Complete viewer data loaded from viewer_data.json.
 *
 * @property {ArtworkMetadata} metadata - Artwork-level metadata (dimensions, artist, scores, etc.)
 * @property {EnrichedStroke[]} strokes - Ordered array of enriched strokes with rendering and context data
 */
export interface ViewerData {
  metadata: ArtworkMetadata;
  strokes: EnrichedStroke[];
}

/**
 * Artwork-level metadata embedded in viewer_data.json.
 *
 * @property {string} artwork_id - Unique identifier for this generation run
 * @property {string} artist_name - Name of the artist style used for generation
 * @property {string} subject - Subject description provided to the VLM
 * @property {number} canvas_width - Canvas width in pixels
 * @property {number} canvas_height - Canvas height in pixels
 * @property {string} background_color - Background color as hex string (e.g. "#FFFFFF")
 * @property {number} total_strokes - Total number of successfully applied strokes
 * @property {number} total_iterations - Total number of VLM query iterations
 * @property {number[]} score_progression - Evaluation score at each iteration (0-100)
 * @property {string} [generation_date] - ISO 8601 timestamp when generation started
 * @property {{ stroke_generator: string; evaluator: string }} [vlm_models] - VLM model identifiers used during generation
 */
export interface ArtworkMetadata {
  artwork_id: string;
  artist_name: string;
  subject: string;
  canvas_width: number;
  canvas_height: number;
  background_color: string;
  total_strokes: number;
  total_iterations: number;
  score_progression: number[];
  generation_date?: string;
  vlm_models?: {
    stroke_generator: string;
    evaluator: string;
  };
}

/**
 * A single stroke enriched with iteration context and batch reasoning.
 *
 * Extends the base Stroke rendering parameters with metadata fields
 * (index, iteration, batch_position, batch_reasoning) added during
 * viewer data export.
 *
 * @property {number} index - Global sequential index (0-based) across all iterations
 * @property {number} iteration - Which VLM query iteration produced this stroke
 * @property {number} batch_position - Position within the iteration's batch (0-based)
 * @property {string} batch_reasoning - VLM's reasoning text for the batch that contains this stroke
 * @property {'line' | 'arc' | 'polyline' | 'circle' | 'splatter'} type - Stroke rendering type
 * @property {string} color_hex - Stroke color as hex string
 * @property {number} thickness - Stroke line thickness in pixels
 * @property {number} opacity - Stroke opacity (0.0 to 1.0)
 * @property {number} [start_x] - Line start X coordinate
 * @property {number} [start_y] - Line start Y coordinate
 * @property {number} [end_x] - Line end X coordinate
 * @property {number} [end_y] - Line end Y coordinate
 * @property {[number, number, number, number]} [arc_bbox] - Arc bounding box [x0, y0, x1, y1]
 * @property {number} [arc_start_angle] - Arc start angle in degrees
 * @property {number} [arc_end_angle] - Arc end angle in degrees
 * @property {[number, number][]} [points] - Array of [x, y] coordinate pairs for polyline vertices
 * @property {number} [center_x] - Circle center X coordinate
 * @property {number} [center_y] - Circle center Y coordinate
 * @property {number} [radius] - Circle radius in pixels
 * @property {boolean} [fill] - Whether the circle is filled (true) or outlined (false)
 * @property {number} [splatter_count] - Number of random dots in the splatter
 * @property {number} [splatter_radius] - Maximum distance from center for splatter dots
 * @property {number} [dot_size_min] - Minimum dot radius in pixels
 * @property {number} [dot_size_max] - Maximum dot radius in pixels
 */
export interface EnrichedStroke {
  index: number;
  iteration: number;
  batch_position: number;
  batch_reasoning: string;
  type: 'line' | 'arc' | 'polyline' | 'circle' | 'splatter';
  color_hex: string;
  thickness: number;
  opacity: number;
  start_x?: number;
  start_y?: number;
  end_x?: number;
  end_y?: number;
  arc_bbox?: [number, number, number, number];
  arc_start_angle?: number;
  arc_end_angle?: number;
  points?: [number, number][];
  center_x?: number;
  center_y?: number;
  radius?: number;
  fill?: boolean;
  splatter_count?: number;
  splatter_radius?: number;
  dot_size_min?: number;
  dot_size_max?: number;
}

/**
 * Summary of an artwork for the homepage gallery.
 *
 * Contains a subset of metadata suitable for rendering a preview
 * card without loading the full stroke data.
 *
 * @property {string} artworkId - Artwork identifier (matches directory name in public/data/)
 * @property {string} artistName - Display name of the artist style
 * @property {string} subject - Subject description
 * @property {number} totalStrokes - Number of strokes in the finished artwork
 * @property {number} totalIterations - Number of VLM iterations used
 * @property {string | null} thumbnailUrl - URL to the thumbnail image, or null if not available
 * @property {string | null} generationDate - ISO 8601 timestamp when generation started, or null if missing
 * @property {string | null} modelName - Stroke generator VLM model name, or null if missing
 */
export interface ArtworkSummary {
  artworkId: string;
  artistName: string;
  subject: string;
  totalStrokes: number;
  totalIterations: number;
  thumbnailUrl: string | null;
  generationDate: string | null;
  modelName: string | null;
}
