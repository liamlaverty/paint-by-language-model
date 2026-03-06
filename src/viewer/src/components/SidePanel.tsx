'use client';

import { useState, useEffect } from 'react';
import { marked } from 'marked';
import { EnrichedStroke, ArtworkMetadata, EvaluationDetail } from '../lib/types';
import { formatDateUK, getScoreColor } from '../lib/format-utils';
import { getPublicUrl } from '../lib/basePath';

/**
 * Props for the stroke metadata side panel.
 *
 * @property {EnrichedStroke | null} stroke - The currently displayed stroke, or null when nothing is selected
 * @property {ArtworkMetadata} metadata - Artwork metadata for header display and score lookup
 * @property {EvaluationDetail[]} [evaluations] - Per-iteration evaluation feedback objects
 * @property {boolean} isLocked - Whether the current stroke selection is click-locked
 * @property {() => void} onClearSelection - Callback to clear the locked selection
 */
interface SidePanelProps {
  stroke: EnrichedStroke | null;
  metadata: ArtworkMetadata;
  evaluations?: EvaluationDetail[];
  isLocked: boolean;
  onClearSelection: () => void;
}

/**
 * Render a markdown string to HTML using `marked`.
 *
 * @param {string} md - Raw markdown content
 * @returns {string} Parsed HTML string
 */
function renderMarkdown(md: string): string {
  return marked.parse(md, { async: false }) as string;
}

/**
 * Stroke metadata side panel component.
 *
 * Provides a three-tab interface: "Run Info" shows artwork-level metadata
 * (artist, subject, canvas size, generation stats, final score),
 * "Stroke Info" shows per-stroke metadata (identity, appearance, geometry,
 * reasoning, score), and "Report" shows the generation report markdown.
 * Auto-switches to Stroke Info when a stroke is selected
 * and back to Run Info when the selection is cleared.
 *
 * @param {SidePanelProps} props - Component props
 * @returns {React.ReactElement} The rendered side panel
 */
export default function SidePanel({
  stroke,
  metadata,
  evaluations = [],
  isLocked,
  onClearSelection,
}: SidePanelProps): React.ReactElement {
  const [activeTab, setActiveTab] = useState<'run' | 'stroke' | 'report'>('run');
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  // Auto-switch tabs when stroke selection changes
  useEffect(() => {
    if (stroke) {
      setActiveTab('stroke');
    } else {
      setActiveTab('run');
    }
  }, [stroke]);

  // Fetch generation report when Report tab is activated
  useEffect(() => {
    if (activeTab === 'report' && reportMarkdown === null) {
      setReportLoading(true);
      fetch(getPublicUrl(`/data/${metadata.artwork_id}/generation_report.md`))
        .then((res) => {
          if (!res.ok) throw new Error('Not found');
          return res.text();
        })
        .then((text) => setReportMarkdown(text))
        .catch(() => setReportMarkdown(''))
        .finally(() => setReportLoading(false));
    }
  }, [activeTab, metadata.artwork_id, reportMarkdown]);

  const finalScore = metadata.final_score ?? 0;
  const scoreColor = getScoreColor(finalScore);

  // Get score at the stroke's iteration (only used when stroke is non-null)
  const scoreAtIteration = stroke ? (metadata.score_progression[stroke.iteration] ?? 0) : 0;
  const scoreBarColor =
    scoreAtIteration < 40 ? '#ef4444' : scoreAtIteration < 70 ? '#f59e0b' : '#22c55e';

  const evaluation = stroke
    ? (evaluations.find((e) => e.iteration === stroke.iteration) ?? null)
    : null;

  return (
    <aside className="side-panel">
      {/* Tab bar */}
      <div className="panel-tabs">
        <button
          className={`panel-tab ${activeTab === 'run' ? 'active' : ''}`}
          onClick={() => setActiveTab('run')}
        >
          Run Info
        </button>
        <button
          className={`panel-tab ${activeTab === 'stroke' ? 'active' : ''}`}
          onClick={() => setActiveTab('stroke')}
        >
          Stroke Info
        </button>
        <button
          className={`panel-tab ${activeTab === 'report' ? 'active' : ''}`}
          onClick={() => setActiveTab('report')}
        >
          Report
        </button>
      </div>

      {/* Clear selection button (shown when locked with a stroke, regardless of tab) */}
      {isLocked && stroke !== null && (
        <button
          type="button"
          className="clear-selection-btn"
          onClick={onClearSelection}
          style={{ display: 'block' }}
        >
          Clear Selection
        </button>
      )}

      {/* Run Info tab content */}
      {activeTab === 'run' && (
        <div className="run-info">
          <h3>Artwork</h3>
          <div className="meta-row-stacked">
            <span className="meta-label-bold">Artist / Style</span>
            <span className="meta-value">{metadata.artist_name}</span>
          </div>
          <div className="meta-row-stacked">
            <span className="meta-label-bold">Subject</span>
            <span className="meta-value">{metadata.subject}</span>
          </div>
          {metadata.expanded_subject && (
            <div className="meta-row-stacked">
              <span className="meta-label-bold">Expanded Subject</span>
              <span className="meta-value">{metadata.expanded_subject}</span>
            </div>
          )}

          <h3>Generation</h3>
          {metadata.generation_date && (
            <div className="meta-row">
              <span className="meta-label">Date</span>
              <span className="meta-value">{formatDateUK(metadata.generation_date)}</span>
            </div>
          )}
          <div className="meta-row">
            <span className="meta-label">Canvas Size</span>
            <span className="meta-value">
              {metadata.canvas_width} × {metadata.canvas_height}
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Total Iterations</span>
            <span className="meta-value">{metadata.total_iterations}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Total Strokes</span>
            <span className="meta-value">{metadata.total_strokes}</span>
          </div>

          <h3>Result</h3>
          <div className="meta-row">
            <span className="meta-label">Final Score</span>
            <span className="meta-value">{finalScore}/100</span>
          </div>
          <div className="score-bar-container">
            <div
              className="score-bar"
              style={{ width: `${finalScore}%`, backgroundColor: scoreColor }}
            />
          </div>
        </div>
      )}

      {/* Stroke Info tab content — stroke selected */}
      {activeTab === 'stroke' && stroke && (
        <>
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

          {/* Evaluation Feedback Section */}
          {evaluation && (
            <>
              <h3>Evaluation Feedback</h3>
              {evaluation.feedback && (
                <>
                  <span className="meta-label">Feedback</span>
                  <div className="reasoning-box">{evaluation.feedback}</div>
                </>
              )}
              {evaluation.strengths && (
                <>
                  <span className="meta-label">Strengths</span>
                  <div className="reasoning-box">{evaluation.strengths}</div>
                </>
              )}
              {evaluation.suggestions && (
                <>
                  <span className="meta-label">Suggestions</span>
                  <div className="reasoning-box">{evaluation.suggestions}</div>
                </>
              )}
            </>
          )}

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

          {stroke.type === 'dry-brush' && (
            <>
              <div className="meta-row">
                <span className="meta-label">Brush Width</span>
                <span className="meta-value">{stroke.brush_width}px</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Bristle Count</span>
                <span className="meta-value">{stroke.bristle_count}</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Gap Probability</span>
                <span className="meta-value">{stroke.gap_probability}</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Point Count</span>
                <span className="meta-value">{stroke.points?.length}</span>
              </div>
            </>
          )}

          {stroke.type === 'chalk' && (
            <>
              <div className="meta-row">
                <span className="meta-label">Chalk Width</span>
                <span className="meta-value">{stroke.chalk_width}px</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Grain Density</span>
                <span className="meta-value">{stroke.grain_density}</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Point Count</span>
                <span className="meta-value">{stroke.points?.length}</span>
              </div>
            </>
          )}

          {stroke.type === 'wet-brush' && (
            <>
              <div className="meta-row">
                <span className="meta-label">Softness</span>
                <span className="meta-value">{stroke.softness}</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Flow</span>
                <span className="meta-value">{stroke.flow}</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Point Count</span>
                <span className="meta-value">{stroke.points?.length}</span>
              </div>
            </>
          )}

          {stroke.type === 'burn' && (
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
                <span className="meta-label">Intensity</span>
                <span className="meta-value">{stroke.intensity}</span>
              </div>
            </>
          )}
        </>
      )}

      {/* Stroke Info tab content — no stroke selected */}
      {activeTab === 'stroke' && !stroke && (
        <div className="hover-hint">
          Hover over a stroke to inspect it. Click a stroke to lock its metadata in place.
        </div>
      )}

      {/* Report tab content */}
      {activeTab === 'report' && (
        <div className="report-content">
          {reportLoading && <p className="loading-hint">Loading report…</p>}
          {!reportLoading && reportMarkdown === '' && (
            <p className="empty-hint">No report available for this artwork.</p>
          )}
          {!reportLoading && reportMarkdown && (
            <div
              className="report-markdown"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(reportMarkdown) }}
            />
          )}
        </div>
      )}
    </aside>
  );
}
