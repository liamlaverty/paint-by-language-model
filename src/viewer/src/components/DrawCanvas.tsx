'use client';

/**
 * DrawCanvas component for interactive stroke drawing.
 *
 * Provides a dual-canvas (main + overlay) surface for building strokes via mouse
 * interactions. The main canvas renders committed strokes; the overlay canvas renders
 * a semi-transparent preview of the in-progress stroke and a crosshair cursor indicator.
 *
 * Supports three interaction modes determined by the active stroke type:
 * - `two-point`: click start, click end (line, arc)
 * - `center-radius`: click centre, click edge (circle, splatter, burn, dodge)
 * - `multi-point`: click to accumulate points, double-click to commit (polyline, chalk, etc.)
 */

import { useRef, useEffect } from 'react';
import type { EnrichedStroke } from '@/lib/types';
import { renderStroke } from '@/lib/renderers';
import { STROKE_INTERACTION, STROKE_DEFAULTS } from '@/lib/draw-types';
import type { DrawStrokeType } from '@/lib/draw-types';

/**
 * Props for the DrawCanvas dual-canvas drawing component.
 *
 * @property {EnrichedStroke[]} strokes - Committed strokes rendered on the main canvas
 * @property {number} canvasWidth - Canvas pixel width
 * @property {number} canvasHeight - Canvas pixel height
 * @property {string} backgroundColor - Background fill colour (hex string)
 * @property {DrawStrokeType} activeType - Stroke type currently selected in the toolbar
 * @property {string} color - Stroke colour as a hex string
 * @property {number} opacity - Stroke opacity (0.0–1.0)
 * @property {number} thickness - Stroke thickness in pixels
 * @property {Partial<EnrichedStroke>} typeParams - Type-specific parameter overrides from toolbar
 * @property {(stroke: EnrichedStroke) => void} onStrokeCommit - Called when a stroke is committed
 */
interface DrawCanvasProps {
  strokes: EnrichedStroke[];
  canvasWidth: number;
  canvasHeight: number;
  backgroundColor: string;
  activeType: DrawStrokeType;
  color: string;
  opacity: number;
  thickness: number;
  typeParams: Partial<EnrichedStroke>;
  onStrokeCommit: (stroke: EnrichedStroke) => void;
}

/**
 * Convert a mouse event's client coordinates to canvas pixel coordinates.
 *
 * Accounts for CSS scaling so that the returned coordinates map correctly
 * to the canvas's intrinsic pixel dimensions even when the canvas element is
 * scaled via CSS (e.g. `width: 100%`).
 *
 * @param {React.MouseEvent<HTMLCanvasElement>} event - Mouse event from the canvas element
 * @param {HTMLCanvasElement} canvas - The target canvas element
 * @returns {{ x: number; y: number }} Canvas-space pixel coordinates (rounded to integers)
 */
function canvasCoords(
  event: React.MouseEvent<HTMLCanvasElement>,
  canvas: HTMLCanvasElement
): { x: number; y: number } {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  return {
    x: Math.round((event.clientX - rect.left) * scaleX),
    y: Math.round((event.clientY - rect.top) * scaleY),
  };
}

/**
 * Construct a complete `EnrichedStroke` from pending click points and toolbar settings.
 *
 * Merges `STROKE_DEFAULTS[type]` first, then `typeParams`, so user overrides win.
 * Geometry fields are set according to the stroke type.
 *
 * @param {DrawStrokeType} type - Stroke type
 * @param {[number, number][]} points - Click points accumulated during the gesture; must contain at least 2 entries for non-multi-point types
 * @param {string} color - Stroke colour hex string
 * @param {number} opacity - Stroke opacity (0.0–1.0)
 * @param {number} thickness - Stroke thickness in pixels
 * @param {Partial<EnrichedStroke>} typeParams - Type-specific overrides from the toolbar
 * @param {number} index - Stroke index (use -1 for preview strokes)
 * @returns {EnrichedStroke} Fully populated stroke ready for rendering or committing
 */
function buildStroke(
  type: DrawStrokeType,
  points: [number, number][],
  color: string,
  opacity: number,
  thickness: number,
  typeParams: Partial<EnrichedStroke>,
  index: number
): EnrichedStroke {
  if (points.length < 2) {
    throw new Error(`buildStroke: at least 2 points required, got ${points.length}`);
  }
  const base: EnrichedStroke = {
    index,
    iteration: 0,
    batch_position: 0,
    batch_reasoning: 'manual',
    type,
    color_hex: color,
    opacity,
    thickness,
    ...STROKE_DEFAULTS[type],
    ...typeParams,
  };

  switch (type) {
    case 'line':
      return {
        ...base,
        start_x: points[0][0],
        start_y: points[0][1],
        end_x: points[1][0],
        end_y: points[1][1],
      };
    case 'burn':
    case 'dodge':
      return {
        ...base,
        center_x: points[0][0],
        center_y: points[0][1],
        radius: Math.hypot(points[1][0] - points[0][0], points[1][1] - points[0][1]),
      };
    case 'arc': {
      // If the user dragged downward, flip to the upper half (n shape) by using
      // 180°–360°. If they dragged upward or sideways, use the lower half (U shape)
      // with 0°–180°. Explicit typeParams overrides always win.
      const draggingDown = points[1][1] > points[0][1];
      const startAngle = typeParams.arc_start_angle ?? (draggingDown ? 180 : 0);
      const endAngle = typeParams.arc_end_angle ?? (draggingDown ? 360 : 180);
      return {
        ...base,
        arc_start_angle: startAngle,
        arc_end_angle: endAngle,
        arc_bbox: [
          Math.min(points[0][0], points[1][0]),
          Math.min(points[0][1], points[1][1]),
          Math.max(points[0][0], points[1][0]),
          Math.max(points[0][1], points[1][1]),
        ],
      };
    }
    case 'polyline':
    case 'dry-brush':
    case 'chalk':
    case 'wet-brush':
      return {
        ...base,
        points,
      };
    case 'circle':
      return {
        ...base,
        center_x: points[0][0],
        center_y: points[0][1],
        radius: Math.hypot(points[1][0] - points[0][0], points[1][1] - points[0][1]),
      };
    case 'splatter':
      return {
        ...base,
        center_x: points[0][0],
        center_y: points[0][1],
        splatter_radius: Math.hypot(points[1][0] - points[0][0], points[1][1] - points[0][1]),
      };
  }
}

/**
 * Draw a small crosshair at the given canvas coordinates.
 *
 * @param {CanvasRenderingContext2D} ctx - Canvas 2D context to draw on
 * @param {number} x - X coordinate for the crosshair centre
 * @param {number} y - Y coordinate for the crosshair centre
 */
function drawCrosshair(ctx: CanvasRenderingContext2D, x: number, y: number): void {
  ctx.save();
  ctx.strokeStyle = '#555';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x - 4, y);
  ctx.lineTo(x + 4, y);
  ctx.moveTo(x, y - 4);
  ctx.lineTo(x, y + 4);
  ctx.stroke();
  ctx.restore();
}

/**
 * Dual-canvas component for interactive stroke drawing.
 *
 * Renders committed strokes on a main canvas and shows a live semi-transparent
 * preview of the in-progress stroke on a transparent overlay canvas. The overlay
 * sits on top and captures all mouse events.
 *
 * @param {DrawCanvasProps} props - Component props
 * @returns {React.JSX.Element} Rendered dual-canvas drawing surface
 */
export default function DrawCanvas({
  strokes,
  canvasWidth,
  canvasHeight,
  backgroundColor,
  activeType,
  color,
  opacity,
  thickness,
  typeParams,
  onStrokeCommit,
}: DrawCanvasProps): React.JSX.Element {
  const mainRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const pendingRef = useRef<{ points: [number, number][] }>({ points: [] });

  // Redraw main canvas whenever strokes or canvas dimensions/background change
  useEffect(() => {
    const canvas = mainRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < strokes.length; i++) {
      renderStroke(ctx, strokes[i], i, false);
    }
  }, [strokes, backgroundColor, canvasWidth, canvasHeight]);

  // Reset in-progress stroke whenever the active stroke type changes
  useEffect(() => {
    pendingRef.current.points = [];
    const canvas = overlayRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
  }, [activeType]);

  // Dismiss the pending stroke when the user clicks outside the canvas
  useEffect(() => {
    function handleOutsideClick(event: MouseEvent): void {
      const canvas = overlayRef.current;
      if (!canvas || pendingRef.current.points.length === 0) return;
      if (!canvas.contains(event.target as Node)) {
        pendingRef.current.points = [];
        const ctx = canvas.getContext('2d');
        if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  /** Commit the given points as a new stroke and reset pending state. */
  const commitStroke = (points: [number, number][]): void => {
    const stroke = buildStroke(
      activeType,
      points,
      color,
      opacity,
      thickness,
      typeParams,
      strokes.length
    );
    onStrokeCommit(stroke);
    pendingRef.current.points = [];
    const canvas = overlayRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  const handleClick = (event: React.MouseEvent<HTMLCanvasElement>): void => {
    const canvas = overlayRef.current;
    if (!canvas) return;

    const { x, y } = canvasCoords(event, canvas);
    const mode = STROKE_INTERACTION[activeType];
    const pending = pendingRef.current;

    if (mode === 'two-point' || mode === 'center-radius') {
      if (pending.points.length === 0) {
        pending.points.push([x, y]);
      } else {
        commitStroke([pending.points[0], [x, y]]);
      }
    } else if (mode === 'multi-point') {
      pending.points.push([x, y]);
    }
  };

  const handleDoubleClick = (_event: React.MouseEvent<HTMLCanvasElement>): void => {
    const canvas = overlayRef.current;
    if (!canvas) return;

    const mode = STROKE_INTERACTION[activeType];
    if (mode !== 'multi-point') return;

    // The double-click fires two click events first, so the last point is a duplicate.
    // Slice it off before committing.
    const pts = pendingRef.current.points.slice(0, -1);
    if (pts.length >= 2) {
      commitStroke(pts);
    } else {
      pendingRef.current.points = [];
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  const handleMouseMove = (event: React.MouseEvent<HTMLCanvasElement>): void => {
    const canvas = overlayRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { x, y } = canvasCoords(event, canvas);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const pending = pendingRef.current;

    if (pending.points.length >= 1) {
      const mode = STROKE_INTERACTION[activeType];
      let previewPoints: [number, number][] | null = null;

      if (mode === 'two-point' || mode === 'center-radius') {
        previewPoints = [pending.points[0], [x, y]];
      } else if (mode === 'multi-point') {
        previewPoints = [...pending.points, [x, y]];
      }

      if (previewPoints && previewPoints.length >= 2) {
        const previewStroke = buildStroke(
          activeType,
          previewPoints,
          color,
          opacity,
          thickness,
          typeParams,
          -1
        );
        ctx.save();
        ctx.globalAlpha = 0.5;
        renderStroke(ctx, previewStroke, -1, false);
        ctx.restore();
      }
    }

    drawCrosshair(ctx, x, y);
  };

  return (
    <div
      className="draw-canvas-container"
      style={{ width: canvasWidth, height: canvasHeight }}
    >
      {/* Main canvas — renders committed strokes with background fill */}
      <canvas
        ref={mainRef}
        className="draw-canvas-main"
        width={canvasWidth}
        height={canvasHeight}
      />
      {/* Overlay canvas — renders in-progress preview; captures all mouse events */}
      <canvas
        ref={overlayRef}
        className="draw-canvas-overlay"
        width={canvasWidth}
        height={canvasHeight}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onMouseMove={handleMouseMove}
      />
    </div>
  );
}
