'use client';

/**
 * DrawPage orchestrator component for the interactive drawing page.
 *
 * Owns all drawing state and connects DrawToolbar and DrawCanvas.
 * Persists the current drawing to localStorage automatically on every change,
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
 * DrawToolbar and DrawCanvas. Persists drawings to localStorage automatically
 * whenever the stroke list or canvas settings change.
 *
 * @returns {React.JSX.Element} The complete draw page layout
 */
export default function DrawPage(): React.JSX.Element {
  const [strokes, setStrokes] = useState<EnrichedStroke[]>([]);
  const [activeType, setActiveType] = useState<DrawStrokeType>('line');
  const [color, setColor] = useState('#000000');
  const [opacity, setOpacity] = useState(1.0);
  const [thickness, setThickness] = useState(4);
  const [typeParams, setTypeParams] = useState<Partial<EnrichedStroke>>({});
  const [canvasWidth] = useState(800);
  const [canvasHeight] = useState(600);
  const [backgroundColor] = useState('#FFFFFF');

  // Tracks whether the initialisation effect has run. Declared as a ref so
  // changes do not trigger re-renders.
  const hasInitialised = useRef(false);

  // Auto-save effect — MUST be declared before the init effect so that on the
  // very first render cycle this effect runs with hasInitialised.current === false
  // and can safely skip saving an empty canvas before loadDrawing has been called.
  useEffect(() => {
    if (!hasInitialised.current && strokes.length === 0) return;
    saveDrawing({
      version: 1,
      canvas_width: canvasWidth,
      canvas_height: canvasHeight,
      background_color: backgroundColor,
      strokes,
    });
  }, [strokes, canvasWidth, canvasHeight, backgroundColor]);

  // Initialisation effect — restore the drawing stored in localStorage on mount.
  useEffect(() => {
    const loaded = loadDrawing();
    if (loaded !== null) {
      setStrokes(loaded.strokes);
    }
    hasInitialised.current = true;
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
      canvas_width: canvasWidth,
      canvas_height: canvasHeight,
      background_color: backgroundColor,
      strokes: newStrokes,
    });
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
      canvas_width: canvasWidth,
      canvas_height: canvasHeight,
      background_color: backgroundColor,
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
        canvas_width: canvasWidth,
        canvas_height: canvasHeight,
        background_color: backgroundColor,
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
              strokes={strokes}
              canvasWidth={canvasWidth}
              canvasHeight={canvasHeight}
              backgroundColor={backgroundColor}
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
            onUpload={handleUpload}
          />
        </div>
      </div>
    </div>
  );
}
