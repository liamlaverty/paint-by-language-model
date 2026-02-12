'use client';

/**
 * StrokeCanvas component for rendering and interacting with artwork strokes.
 *
 * Manages a triple-canvas stack: main (visible), hit (unique colors for detection),
 * and overlay (transparent highlight layer). Handles mouse hover/click detection
 * by reading pixel colors from the hidden hit canvas.
 */

import { useRef, useEffect } from 'react';
import type { EnrichedStroke, ArtworkMetadata } from '@/lib/types';
import { renderStroke } from '@/lib/stroke-renderers';
import { getStrokeIndexAtPoint } from '@/lib/hit-detection';

/**
 * Props for the StrokeCanvas triple-canvas component.
 *
 * @property {EnrichedStroke[]} strokes - Array of all enriched strokes for the artwork
 * @property {ArtworkMetadata} metadata - Artwork metadata (canvas dimensions, background color)
 * @property {number} visibleCount - Number of strokes currently rendered on canvas
 * @property {(index: number) => void} onStrokeHover - Callback when a stroke is hovered (receives stroke index, -1 for none)
 * @property {(index: number) => void} onStrokeClick - Callback when a stroke is clicked (receives stroke index)
 * @property {() => void} onBackgroundClick - Callback when background (no stroke) is clicked
 * @property {number} lockedIndex - Index of the currently locked stroke (-1 for none)
 * @property {number} highlightedIndex - Index of the currently highlighted stroke (-1 for none)
 */
interface StrokeCanvasProps {
  /** Array of all enriched strokes for the artwork */
  strokes: EnrichedStroke[];
  /** Artwork metadata (canvas dimensions, background color) */
  metadata: ArtworkMetadata;
  /** Number of strokes currently rendered on canvas */
  visibleCount: number;
  /** Callback when a stroke is hovered (receives stroke index, -1 for none) */
  onStrokeHover: (index: number) => void;
  /** Callback when a stroke is clicked (receives stroke index) */
  onStrokeClick: (index: number) => void;
  /** Callback when background (no stroke) is clicked */
  onBackgroundClick: () => void;
  /** Index of the currently locked stroke (-1 for none) */
  lockedIndex: number;
  /** Index of the currently highlighted stroke (-1 for none) */
  highlightedIndex: number;
}

/**
 * Triple-canvas component for stroke rendering, hit detection, and highlighting.
 *
 * Manages three stacked HTML5 canvases:
 * 1. Main canvas - Visible rendering with actual stroke colors and opacity
 * 2. Hit canvas - Hidden canvas with unique solid colors per stroke for pixel-based detection
 * 3. Overlay canvas - Transparent layer for rendering hover/selection highlights
 *
 * Mouse interactions read pixels from the hit canvas to determine which stroke
 * (if any) is under the cursor, enabling precise hover and click detection.
 *
 * @param {StrokeCanvasProps} props - Component props
 * @returns {React.JSX.Element} Rendered triple-canvas stack
 */
export default function StrokeCanvas({
  strokes,
  metadata,
  visibleCount,
  onStrokeHover,
  onStrokeClick,
  onBackgroundClick,
  lockedIndex,
  highlightedIndex,
}: StrokeCanvasProps): React.JSX.Element {
  const mainRef = useRef<HTMLCanvasElement>(null);
  const hitRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);

  // Effect: Redraw main and hit canvases when visibleCount changes
  useEffect(() => {
    const mainCanvas = mainRef.current;
    const hitCanvas = hitRef.current;

    if (!mainCanvas || !hitCanvas) return;

    const mainCtx = mainCanvas.getContext('2d');
    const hitCtx = hitCanvas.getContext('2d');

    if (!mainCtx || !hitCtx) return;

    // Clear main canvas with background color
    mainCtx.fillStyle = metadata.background_color || '#FFFFFF';
    mainCtx.fillRect(0, 0, mainCanvas.width, mainCanvas.height);

    // Clear hit canvas with black (background)
    hitCtx.fillStyle = '#000000';
    hitCtx.fillRect(0, 0, hitCanvas.width, hitCanvas.height);
    // Disable anti-aliasing on hit canvas for precise color reads
    hitCtx.imageSmoothingEnabled = false;

    // Render strokes on both canvases
    for (let i = 0; i < visibleCount && i < strokes.length; i++) {
      renderStroke(mainCtx, strokes[i], i, false); // Visual render
      renderStroke(hitCtx, strokes[i], i, true); // Hit detection render
    }
  }, [strokes, metadata, visibleCount]);

  // Effect: Redraw overlay canvas when highlightedIndex changes
  useEffect(() => {
    const overlayCanvas = overlayRef.current;
    if (!overlayCanvas) return;

    const overlayCtx = overlayCanvas.getContext('2d');
    if (!overlayCtx) return;

    // Clear overlay
    overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    // If a stroke is highlighted and visible, draw highlight
    if (highlightedIndex >= 0 && highlightedIndex < visibleCount) {
      const stroke = strokes[highlightedIndex];

      overlayCtx.save();
      overlayCtx.globalAlpha = 0.6;
      overlayCtx.shadowColor = '#e94560';
      overlayCtx.shadowBlur = 12;

      // Render stroke in highlight color with increased thickness
      const originalThickness = stroke.thickness;

      // Temporarily modify stroke for highlight appearance
      const highlightStroke = {
        ...stroke,
        color_hex: '#e94560',
        opacity: 1.0,
        thickness: Math.max(originalThickness + 2, 4),
      };

      renderStroke(overlayCtx, highlightStroke, highlightedIndex, false);
      overlayCtx.restore();
    }
  }, [strokes, highlightedIndex, visibleCount]);

  // Mouse move handler: detect stroke under cursor
  const handleMouseMove = (event: React.MouseEvent<HTMLCanvasElement>): void => {
    // Skip hover detection if a stroke is locked
    if (lockedIndex !== -1) return;

    const mainCanvas = mainRef.current;
    const hitCanvas = hitRef.current;

    if (!mainCanvas || !hitCanvas) return;

    const hitCtx = hitCanvas.getContext('2d');
    if (!hitCtx) return;

    const rect = mainCanvas.getBoundingClientRect();
    const clientX = event.clientX - rect.left;
    const clientY = event.clientY - rect.top;

    const strokeIndex = getStrokeIndexAtPoint(hitCtx, hitCanvas, clientX, clientY);

    // Only trigger hover for visible strokes
    if (strokeIndex >= 0 && strokeIndex < visibleCount) {
      onStrokeHover(strokeIndex);
    } else {
      onStrokeHover(-1);
    }
  };

  // Click handler: trigger click callback for stroke or background
  const handleClick = (event: React.MouseEvent<HTMLCanvasElement>): void => {
    const mainCanvas = mainRef.current;
    const hitCanvas = hitRef.current;

    if (!mainCanvas || !hitCanvas) return;

    const hitCtx = hitCanvas.getContext('2d');
    if (!hitCtx) return;

    const rect = mainCanvas.getBoundingClientRect();
    const clientX = event.clientX - rect.left;
    const clientY = event.clientY - rect.top;

    const strokeIndex = getStrokeIndexAtPoint(hitCtx, hitCanvas, clientX, clientY);

    if (strokeIndex >= 0 && strokeIndex < visibleCount) {
      onStrokeClick(strokeIndex);
    } else {
      onBackgroundClick();
    }
  };

  // Mouse leave handler: clear hover unless locked
  const handleMouseLeave = (): void => {
    if (lockedIndex !== -1) return;
    onStrokeHover(-1);
  };

  return (
    <div
      style={{
        position: 'relative',
        width: metadata.canvas_width,
        height: metadata.canvas_height,
        display: 'inline-block',
      }}
    >
      {/* Main canvas - visible rendering */}
      <canvas
        ref={mainRef}
        width={metadata.canvas_width}
        height={metadata.canvas_height}
        onMouseMove={handleMouseMove}
        onClick={handleClick}
        onMouseLeave={handleMouseLeave}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          cursor: 'crosshair',
          border: '1px solid var(--color-border)',
        }}
      />

      {/* Hit canvas - hidden unique-color detection */}
      <canvas
        ref={hitRef}
        width={metadata.canvas_width}
        height={metadata.canvas_height}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          display: 'none',
        }}
      />

      {/* Overlay canvas - transparent highlight layer */}
      <canvas
        ref={overlayRef}
        width={metadata.canvas_width}
        height={metadata.canvas_height}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}
