'use client';

/**
 * DrawToolbar component — horizontal control bar for the interactive draw page.
 *
 * Contains stroke-type selection, colour/opacity/thickness controls,
 * type-specific advanced parameters, and action buttons (undo, redo, clear,
 * download, upload).  All state is managed by the parent and passed in via props.
 */

import { useRef } from 'react';
import {
  STROKE_TYPES,
  STROKE_DEFAULTS,
  STROKE_INTERACTION,
  type DrawStrokeType,
} from '@/lib/draw-types';
import type { EnrichedStroke } from '@/lib/types';

/** Human-readable description for each stroke type, shown alongside the type selector. */
const STROKE_DESCRIPTIONS: Record<DrawStrokeType, string> = {
  line: 'Draw a straight line between two points.',
  arc: 'Draw a curved arc within a bounding rectangle.',
  polyline: 'Draw a freeform path through multiple points.',
  circle: 'Draw a circle defined by a centre point and radius.',
  splatter: 'Scatter paint droplets around a centre point.',
  'dry-brush': 'Apply a multi-line stroke with multiple bristles, mimicking a dry brush.',
  chalk: 'Draw a textured chalk stroke with grain and soft edges.',
  'wet-brush': 'Paint with a soft, bleeding edge that simulates wet paint.',
  burn: 'Darken a circular region of the canvas.',
  dodge: 'Lighten a circular region of the canvas.',
};

/**
 * Props for the DrawToolbar component.
 *
 * @property {DrawStrokeType} activeType - Currently selected stroke type
 * @property {(type: DrawStrokeType) => void} onTypeChange - Callback when stroke type selection changes
 * @property {string} color - Current stroke colour as a hex string
 * @property {(hex: string) => void} onColorChange - Callback when colour changes
 * @property {number} opacity - Current stroke opacity (0–1)
 * @property {(value: number) => void} onOpacityChange - Callback when opacity changes
 * @property {number} thickness - Current stroke thickness in pixels
 * @property {(value: number) => void} onThicknessChange - Callback when thickness changes
 * @property {Partial<EnrichedStroke>} typeParams - Current type-specific parameter overrides
 * @property {(params: Partial<EnrichedStroke>) => void} onTypeParamsChange - Callback when type-specific params change
 * @property {() => void} onClear - Callback to clear the canvas
 * @property {() => void} onDownload - Callback to download the drawing as JSON
 * @property {() => void} onDownloadJPG - Callback to download the canvas as a JPEG image
 * @property {boolean} canDownloadJPG - Whether the JPEG download button should be enabled (true when strokes exist)
 * @property {(json: string) => void} onUpload - Callback receiving uploaded JSON file text
 */
interface DrawToolbarProps {
  activeType: DrawStrokeType;
  onTypeChange: (type: DrawStrokeType) => void;
  color: string;
  onColorChange: (hex: string) => void;
  opacity: number;
  onOpacityChange: (value: number) => void;
  thickness: number;
  onThicknessChange: (value: number) => void;
  typeParams: Partial<EnrichedStroke>;
  onTypeParamsChange: (params: Partial<EnrichedStroke>) => void;
  onClear: () => void;
  onDownload: () => void;
  onDownloadJPG: () => void;
  canDownloadJPG: boolean;
  onUpload: (json: string) => void;
}

/**
 * Toolbar component for the interactive draw page.
 *
 * Renders a horizontal bar with stroke-type buttons, common paint controls
 * (colour, opacity, thickness), type-specific advanced parameters, and
 * action buttons (clear, download, upload JSON).
 *
 * @param {DrawToolbarProps} props - Component props
 * @returns {React.JSX.Element} The rendered toolbar
 */
export default function DrawToolbar({
  activeType,
  onTypeChange,
  color,
  onColorChange,
  opacity,
  onOpacityChange,
  thickness,
  onThicknessChange,
  typeParams,
  onTypeParamsChange,
  onClear,
  onDownload,
  onDownloadJPG,
  canDownloadJPG,
  onUpload,
}: DrawToolbarProps): React.JSX.Element {
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>): void {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        onUpload(reader.result);
      }
    };
    reader.readAsText(file);
    // Reset so the same file can be re-uploaded if needed
    e.target.value = '';
  }

  const activeDefaults = STROKE_DEFAULTS[activeType];
  const hasAdvancedParams = Object.keys(activeDefaults).length > 0 || activeType === 'arc';

  const interactionMode = STROKE_INTERACTION[activeType];

  return (
    <div className="draw-toolbar side-panel">
      {/* ── Stroke Type ── */}
      <h3>Stroke Type</h3>
      <div className="draw-toolbar-types">
        {STROKE_TYPES.map((type) => (
          <button
            key={type}
            type="button"
            className={`button draw-toolbar-type-btn${type === activeType ? ' active' : ''}`}
            onClick={() => onTypeChange(type)}
          >
            {type}
          </button>
        ))}
      </div>

      {/* ── Stroke Config ── */}
      <h3>Stroke Config</h3>
      {/* Common controls: colour, opacity, thickness */}
      <div className="draw-toolbar-controls">
        <label className="draw-toolbar-control">
          Colour
          <input type="color" value={color} onChange={(e) => onColorChange(e.target.value)} />
        </label>

        <label className="draw-toolbar-control">
          Opacity
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={opacity}
            onChange={(e) => onOpacityChange(Number(e.target.value))}
          />
          <span>{opacity.toFixed(2)}</span>
        </label>

        <label className="draw-toolbar-control">
          Thickness
          <input
            type="range"
            min="1"
            max="50"
            value={thickness}
            onChange={(e) => onThicknessChange(Number(e.target.value))}
          />
          <span>{thickness}</span>
        </label>
      </div>

      {/* Advanced parameters — only shown for stroke types that have type-specific defaults */}
      {hasAdvancedParams && (
        <div className="draw-toolbar-advanced">
          {activeType === 'arc' && (
            <>
              <label className="draw-toolbar-advanced-param">
                Start Angle
                <input
                  type="range"
                  min="0"
                  max="360"
                  value={typeParams.arc_start_angle ?? activeDefaults.arc_start_angle ?? 0}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      arc_start_angle: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.arc_start_angle ?? activeDefaults.arc_start_angle ?? 0}</span>
              </label>
              <label className="draw-toolbar-advanced-param">
                End Angle
                <input
                  type="range"
                  min="0"
                  max="360"
                  value={typeParams.arc_end_angle ?? activeDefaults.arc_end_angle ?? 180}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      arc_end_angle: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.arc_end_angle ?? activeDefaults.arc_end_angle ?? 180}</span>
              </label>
            </>
          )}

          {activeType === 'circle' && (
            <label className="draw-toolbar-advanced-param">
              Fill
              <input
                type="checkbox"
                checked={typeParams.fill ?? activeDefaults.fill ?? false}
                onChange={(e) => onTypeParamsChange({ ...typeParams, fill: e.target.checked })}
              />
            </label>
          )}

          {activeType === 'splatter' && (
            <>
              <label className="draw-toolbar-advanced-param">
                Splatter Count
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={typeParams.splatter_count ?? activeDefaults.splatter_count ?? 30}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      splatter_count: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.splatter_count ?? activeDefaults.splatter_count ?? 30}</span>
              </label>
              <label className="draw-toolbar-advanced-param">
                Dot Size Min
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={typeParams.dot_size_min ?? activeDefaults.dot_size_min ?? 1}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      dot_size_min: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.dot_size_min ?? activeDefaults.dot_size_min ?? 1}</span>
              </label>
              <label className="draw-toolbar-advanced-param">
                Dot Size Max
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={typeParams.dot_size_max ?? activeDefaults.dot_size_max ?? 4}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      dot_size_max: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.dot_size_max ?? activeDefaults.dot_size_max ?? 4}</span>
              </label>
            </>
          )}

          {activeType === 'dry-brush' && (
            <>
              <label className="draw-toolbar-advanced-param">
                Brush Width
                <input
                  type="range"
                  min="5"
                  max="60"
                  value={typeParams.brush_width ?? activeDefaults.brush_width ?? 20}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      brush_width: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.brush_width ?? activeDefaults.brush_width ?? 20}</span>
              </label>
              <label className="draw-toolbar-advanced-param">
                Bristle Count
                <input
                  type="range"
                  min="2"
                  max="20"
                  value={typeParams.bristle_count ?? activeDefaults.bristle_count ?? 8}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      bristle_count: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.bristle_count ?? activeDefaults.bristle_count ?? 8}</span>
              </label>
              <label className="draw-toolbar-advanced-param">
                Gap Probability
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={typeParams.gap_probability ?? activeDefaults.gap_probability ?? 0.3}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      gap_probability: Number(e.target.value),
                    })
                  }
                />
                <span>
                  {(typeParams.gap_probability ?? activeDefaults.gap_probability ?? 0.3).toFixed(2)}
                </span>
              </label>
            </>
          )}

          {activeType === 'chalk' && (
            <>
              <label className="draw-toolbar-advanced-param">
                Chalk Width
                <input
                  type="range"
                  min="4"
                  max="40"
                  value={typeParams.chalk_width ?? activeDefaults.chalk_width ?? 12}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      chalk_width: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.chalk_width ?? activeDefaults.chalk_width ?? 12}</span>
              </label>
              <label className="draw-toolbar-advanced-param">
                Grain Density
                <input
                  type="range"
                  min="10"
                  max="100"
                  value={typeParams.grain_density ?? activeDefaults.grain_density ?? 10}
                  onChange={(e) =>
                    onTypeParamsChange({
                      ...typeParams,
                      grain_density: Number(e.target.value),
                    })
                  }
                />
                <span>{typeParams.grain_density ?? activeDefaults.grain_density ?? 40}</span>
              </label>
            </>
          )}

          {activeType === 'wet-brush' && (
            <>
              <label className="draw-toolbar-advanced-param">
                Softness
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={typeParams.softness ?? activeDefaults.softness ?? 3}
                  onChange={(e) =>
                    onTypeParamsChange({ ...typeParams, softness: Number(e.target.value) })
                  }
                />
                <span>{typeParams.softness ?? activeDefaults.softness ?? 3}</span>
              </label>
              <label className="draw-toolbar-advanced-param">
                Flow
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={typeParams.flow ?? activeDefaults.flow ?? 0.8}
                  onChange={(e) =>
                    onTypeParamsChange({ ...typeParams, flow: Number(e.target.value) })
                  }
                />
                <span>{(typeParams.flow ?? activeDefaults.flow ?? 0.8).toFixed(1)}</span>
              </label>
            </>
          )}

          {(activeType === 'burn' || activeType === 'dodge') && (
            <label className="draw-toolbar-advanced-param">
              Intensity
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.05"
                value={typeParams.intensity ?? activeDefaults.intensity ?? 0.3}
                onChange={(e) =>
                  onTypeParamsChange({ ...typeParams, intensity: Number(e.target.value) })
                }
              />
              <span>{(typeParams.intensity ?? activeDefaults.intensity ?? 0.3).toFixed(2)}</span>
            </label>
          )}
        </div>
      )}

      {/* ── Instructions ── */}
      <h3>Instructions</h3>
      <ul className="draw-toolbar-instructions">
        <li>{STROKE_DESCRIPTIONS[activeType]}</li>
        {interactionMode === 'two-point' && (
          <li>
            Click to place the <strong>start point</strong>, then click again to place the{' '}
            <strong>end point</strong>.
          </li>
        )}
        {interactionMode === 'center-radius' && (
          <li>
            Click to place the <strong>centre</strong>, then click again to set the{' '}
            <strong>radius</strong>.
          </li>
        )}
        {interactionMode === 'multi-point' && (
          <>
            <li>Click to add points to the stroke.</li>
            <li>
              <strong>Double-click</strong> to finish and commit the stroke.
            </li>
          </>
        )}
        <li>
          Click outside the canvas to <strong>dismiss</strong> an in-progress stroke.
        </li>
      </ul>

      {/* ── Canvas Tools ── */}
      <h3>Canvas Tools</h3>
      {/* Action buttons */}
      <div className="draw-toolbar-actions">
        <button type="button" className="button" onClick={onClear}>
          Clear
        </button>
        <button type="button" className="button" onClick={onDownload}>
          Download JSON
        </button>
        <button type="button" className="button" onClick={onDownloadJPG} disabled={!canDownloadJPG}>
          Download JPG
        </button>
        <button type="button" className="button" onClick={() => fileInputRef.current?.click()}>
          Upload JSON
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </div>
    </div>
  );
}
