'use client';

/**
 * DrawPage orchestrator component for the interactive drawing page.
 *
 * Owns all drawing state and connects DrawToolbar and DrawCanvas.
 * Persists the current drawing to localStorage on every committed stroke,
 * and restores it on mount.
 */

import { useState, useEffect, useRef } from 'react';
import type { EnrichedStroke } from '@/lib/types';
import { STROKE_DEFAULTS, type DrawStrokeType, type DrawingData } from '@/lib/draw-types';
import {
  saveDrawing,
  loadDrawing,
  clearDrawing,
  exportDrawingJSON,
  importDrawingJSON,
} from '@/lib/draw-persistence';
import DrawToolbar from './DrawToolbar';
import DrawCanvas from './DrawCanvas';

/**
 * Orchestrator component for the interactive draw page.
 *
 * Manages all drawing state (strokes, tool settings) and wires together
 * DrawToolbar and DrawCanvas. Persists the drawing to localStorage on every
 * committed stroke via handleStrokeCommit.
 *
 * @returns {React.JSX.Element} The complete draw page layout
 */
const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;
const BACKGROUND_COLOR = '#FFFFFF';

export default function DrawPage(): React.JSX.Element {
  const [strokes, setStrokes] = useState<EnrichedStroke[]>([]);
  const [activeType, setActiveType] = useState<DrawStrokeType>('line');
  const [color, setColor] = useState('#000000');
  const [opacity, setOpacity] = useState(1.0);
  const [thickness, setThickness] = useState(4);
  const [typeParams, setTypeParams] = useState<Partial<EnrichedStroke>>({});

  /** Ref to the main canvas element in DrawCanvas, used for JPEG export. */
  const canvasRef = useRef<HTMLCanvasElement>(null);

  /** True when there is at least one committed stroke; enables the Download JPG button. */
  const canDownloadJPG = strokes.length > 0;

  // Initialisation effect — restore the drawing stored in localStorage on mount.
  useEffect(() => {
    const loaded = loadDrawing();
    if (loaded !== null) {
      setStrokes(loaded.strokes);
    }
  }, []);

  // Reset type-specific parameter overrides whenever the active stroke type changes.
  useEffect(() => {
    setTypeParams({ ...STROKE_DEFAULTS[activeType] });
  }, [activeType]);

  /**
   * Commit a completed stroke: append to the stroke list and persist to localStorage.
   *
   * @param {EnrichedStroke} stroke - The newly completed stroke to commit
   */
  function handleStrokeCommit(stroke: EnrichedStroke): void {
    const newStrokes = [...strokes, stroke];
    setStrokes(newStrokes);
    saveDrawing({
      version: 1,
      canvas_width: CANVAS_WIDTH,
      canvas_height: CANVAS_HEIGHT,
      background_color: BACKGROUND_COLOR,
      strokes: newStrokes,
    });
  }

  /**
   * Download the current canvas as a JPEG file.
   *
   * Reads the main canvas element via canvasRef, encodes it as a JPEG data URL
   * (quality 0.92), then triggers a browser file-download via a temporary anchor
   * element. The canvas background is always white, so no compositing is needed.
   */
  function handleDownloadJPG(): void {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = 'drawing.jpg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  /**
   * Clear the canvas after user confirmation.
   *
   * Resets strokes to an empty array and removes the drawing from localStorage
   * via clearDrawing().
   */
  function handleClear(): void {
    if (!window.confirm('Clear the canvas? This cannot be undone.')) return;
    setStrokes([]);
    clearDrawing();
  }

  /**
   * Download the current drawing as a JSON file.
   *
   * Builds a DrawingData object, serialises it via exportDrawingJSON, creates
   * a Blob, and triggers a browser file-download via a temporary anchor element.
   */
  function handleDownload(): void {
    const data: DrawingData = {
      version: 1,
      canvas_width: CANVAS_WIDTH,
      canvas_height: CANVAS_HEIGHT,
      background_color: BACKGROUND_COLOR,
      strokes,
    };
    const json = exportDrawingJSON(data);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'drawing.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Import a drawing from uploaded JSON text.
   *
   * Calls importDrawingJSON to parse and validate the text. If valid, replaces
   * the current strokes with the imported ones and persists. If invalid, shows
   * an alert to the user.
   *
   * @param {string} json - Raw JSON text from the uploaded file
   */
  function handleUpload(json: string): void {
    const result = importDrawingJSON(json);
    if (result !== null) {
      setStrokes(result.strokes);
      saveDrawing({
        version: 1,
        canvas_width: CANVAS_WIDTH,
        canvas_height: CANVAS_HEIGHT,
        background_color: BACKGROUND_COLOR,
        strokes: result.strokes,
      });
    } else {
      alert('Invalid drawing file. Expected a valid Paint by Language Model drawing JSON.');
    }
  }

  return (
    <div className="viewer-container">
      <div className="content-grid">
        <div className="left-panel">
          <div className="canvas-container">
            <DrawCanvas
              ref={canvasRef}
              strokes={strokes}
              canvasWidth={CANVAS_WIDTH}
              canvasHeight={CANVAS_HEIGHT}
              backgroundColor={BACKGROUND_COLOR}
              activeType={activeType}
              color={color}
              opacity={opacity}
              thickness={thickness}
              typeParams={typeParams}
              onStrokeCommit={handleStrokeCommit}
            />
          </div>
        </div>
        <div className="right-panel">
          <DrawToolbar
            activeType={activeType}
            onTypeChange={setActiveType}
            color={color}
            onColorChange={setColor}
            opacity={opacity}
            onOpacityChange={setOpacity}
            thickness={thickness}
            onThicknessChange={setThickness}
            typeParams={typeParams}
            onTypeParamsChange={setTypeParams}
            onClear={handleClear}
            onDownload={handleDownload}
            onDownloadJPG={handleDownloadJPG}
            canDownloadJPG={canDownloadJPG}
            onUpload={handleUpload}
          />
        </div>
      </div>
    </div>
  );
}
