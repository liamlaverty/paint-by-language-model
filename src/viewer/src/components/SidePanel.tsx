'use client';

import { EnrichedStroke, ArtworkMetadata } from '../lib/types';

/**
 * Props for the stroke metadata side panel.
 *
 * @property {EnrichedStroke | null} stroke - The currently displayed stroke, or null when nothing is selected
 * @property {ArtworkMetadata} metadata - Artwork metadata for header display and score lookup
 * @property {boolean} isLocked - Whether the current stroke selection is click-locked
 * @property {() => void} onClearSelection - Callback to clear the locked selection
 */
interface SidePanelProps {
  stroke: EnrichedStroke | null;
  metadata: ArtworkMetadata;
  isLocked: boolean;
  onClearSelection: () => void;
}

/**
 * Stroke metadata side panel component.
 *
 * Displays artwork header and hover hint when no stroke is selected, or full
 * stroke metadata (identity, appearance, geometry, reasoning, score) when a
 * stroke is hovered or locked. Supports all stroke types with type-specific
 * geometry sections.
 *
 * @param {SidePanelProps} props - Component props
 * @returns {React.ReactElement} The rendered side panel
 */
export default function SidePanel({
  stroke,
  metadata,
  isLocked,
  onClearSelection,
}: SidePanelProps): React.ReactElement {
  // No stroke selected — show artwork header and hover hint
  if (!stroke) {
    return (
      <aside className="side-panel">
        <div className="artwork-header">
          <div className="title">
            {metadata.artist_name} · {metadata.artwork_id}
          </div>
          <div className="subtitle">{metadata.subject}</div>
        </div>
        <div className="hover-hint">
          Hover over a stroke to inspect it. Click a stroke to lock its metadata in place.
        </div>
      </aside>
    );
  }

  // Get score at the stroke's iteration
  const scoreAtIteration = metadata.score_progression[stroke.iteration] ?? 0;
  const scoreBarColor =
    scoreAtIteration < 40 ? '#ef4444' : scoreAtIteration < 70 ? '#f59e0b' : '#22c55e';

  return (
    <aside className="side-panel">
      {/* Clear selection button (shown when locked) */}
      {isLocked && (
        <button
          type="button"
          className="clear-selection-btn"
          onClick={onClearSelection}
          style={{ display: 'block' }}
        >
          Clear Selection
        </button>
      )}

      {/* Stroke header */}
      <div className="stroke-info">
        <h2>
          Stroke {stroke.index + 1} of {metadata.total_strokes}
          {isLocked && <span className="locked-badge">Locked</span>}
        </h2>
      </div>

      {/* Identity Section */}
      <h3>Identity</h3>
      <div className="meta-row">
        <span className="meta-label">Type</span>
        <span className="meta-value">{stroke.type}</span>
      </div>
      <div className="meta-row">
        <span className="meta-label">Iteration</span>
        <span className="meta-value">
          {stroke.iteration + 1} of {metadata.total_iterations}
        </span>
      </div>
      <div className="meta-row">
        <span className="meta-label">Batch Position</span>
        <span className="meta-value">{stroke.batch_position}</span>
      </div>

      {/* Appearance Section */}
      <h3>Appearance</h3>
      <div className="meta-row">
        <span className="meta-label">Color</span>
        <span className="meta-value">
          <span className="color-swatch" style={{ backgroundColor: stroke.color_hex }} />
          {stroke.color_hex}
        </span>
      </div>
      <div className="meta-row">
        <span className="meta-label">Opacity</span>
        <span className="meta-value">{Math.round(stroke.opacity * 100)}%</span>
      </div>
      <div className="meta-row">
        <span className="meta-label">Thickness</span>
        <span className="meta-value">{stroke.thickness}px</span>
      </div>

      {/* Geometry Section (type-specific) */}
      <h3>Geometry</h3>
      {stroke.type === 'line' && (
        <>
          <div className="meta-row">
            <span className="meta-label">Start</span>
            <span className="meta-value">
              ({stroke.start_x}, {stroke.start_y})
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">End</span>
            <span className="meta-value">
              ({stroke.end_x}, {stroke.end_y})
            </span>
          </div>
        </>
      )}

      {stroke.type === 'arc' && stroke.arc_bbox && (
        <>
          <div className="meta-row">
            <span className="meta-label">Bbox</span>
            <span className="meta-value">
              [{stroke.arc_bbox[0]}, {stroke.arc_bbox[1]}, {stroke.arc_bbox[2]},{' '}
              {stroke.arc_bbox[3]}]
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Angles</span>
            <span className="meta-value">
              {stroke.arc_start_angle}° → {stroke.arc_end_angle}°
            </span>
          </div>
        </>
      )}

      {stroke.type === 'polyline' && stroke.points && (
        <>
          <div className="meta-row">
            <span className="meta-label">Point Count</span>
            <span className="meta-value">{stroke.points.length}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Path</span>
            <span className="meta-value">
              {stroke.points
                .slice(0, 4)
                .map((p) => `(${p[0]},${p[1]})`)
                .join(' ')}
              {stroke.points.length > 4 && ' …'}
            </span>
          </div>
        </>
      )}

      {stroke.type === 'circle' && (
        <>
          <div className="meta-row">
            <span className="meta-label">Center</span>
            <span className="meta-value">
              ({stroke.center_x}, {stroke.center_y})
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Radius</span>
            <span className="meta-value">{stroke.radius}px</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Fill</span>
            <span className="meta-value">{stroke.fill ? 'Solid' : 'Outline'}</span>
          </div>
        </>
      )}

      {stroke.type === 'splatter' && (
        <>
          <div className="meta-row">
            <span className="meta-label">Center</span>
            <span className="meta-value">
              ({stroke.center_x}, {stroke.center_y})
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Radius</span>
            <span className="meta-value">{stroke.splatter_radius}px</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Dot Count</span>
            <span className="meta-value">{stroke.splatter_count}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Dot Size Range</span>
            <span className="meta-value">
              {stroke.dot_size_min}–{stroke.dot_size_max}px
            </span>
          </div>
        </>
      )}

      {/* Batch Reasoning Section */}
      <h3>Batch Reasoning</h3>
      <div className="reasoning-box">{stroke.batch_reasoning}</div>

      {/* Score at Iteration Section */}
      <h3>Score at Iteration</h3>
      <div className="meta-row">
        <span className="meta-label">Evaluation Score</span>
        <span className="meta-value">{scoreAtIteration}/100</span>
      </div>
      <div className="score-bar-container">
        <div
          className="score-bar"
          style={{
            width: `${scoreAtIteration}%`,
            backgroundColor: scoreBarColor,
          }}
        />
      </div>
    </aside>
  );
}
