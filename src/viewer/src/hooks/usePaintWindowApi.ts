'use client';

/**
 * usePaintWindowApi — registers window.paintByLanguageModel on mount, removes it on unmount.
 *
 * Accepts React state setters and refs from DrawPage and exposes all 17 API methods
 * as a plain object on the global window. Non-enumerable to avoid polluting autocomplete.
 */

import { useEffect, useRef } from 'react';
import type { RefObject } from 'react';
import type { EnrichedStroke } from '@/lib/types';
import { STROKE_TYPES, STROKE_DEFAULTS, type DrawStrokeType } from '@/lib/draw-types';
import type { DrawCanvasHandle } from '@/components/DrawCanvas';

/**
 * Full TypeScript shape of the window.paintByLanguageModel API object.
 *
 * Consumers (e.g. browser-console scripts or Playwright agents) can cast
 * `(window as any).paintByLanguageModel` to this type for IDE autocomplete.
 */
export interface PaintWindowApi {
  selectStrokeType(type: string): void;
  setColor(hex: string): void;
  setOpacity(value: number): void;
  setThickness(px: number): void;
  setTypeParam(key: string, value: unknown): void;
  click(x: number, y: number): void;
  doubleClick(x: number, y: number): void;
  cancelStroke(): void;
  clearCanvas(): void;
  getStrokes(): object[];
  loadStrokes(drawingJson: string): void;
  downloadJSON(): void;
  downloadJPG(): void;
  getCanvasImageDataUrl(): string;
  getState(): {
    activeType: string;
    color: string;
    opacity: number;
    thickness: number;
    typeParams: object;
    strokeCount: number;
  };
  getStrokeTypes(): string[];
  getTypeParamSchema(type: string): object;
}

/**
 * Parameters accepted by usePaintWindowApi.
 *
 * @property {(t: DrawStrokeType) => void} setActiveType - Setter for the active stroke type
 * @property {(hex: string) => void} setColor - Setter for stroke colour
 * @property {(v: number) => void} setOpacity - Setter for stroke opacity
 * @property {(px: number) => void} setThickness - Setter for stroke thickness
 * @property {(p: Partial<EnrichedStroke>) => void} setTypeParams - Setter for type-specific params
 * @property {() => DrawStrokeType} getActiveType - Returns the current active stroke type
 * @property {() => string} getColor - Returns the current stroke colour
 * @property {() => number} getOpacity - Returns the current stroke opacity
 * @property {() => number} getThickness - Returns the current stroke thickness
 * @property {() => EnrichedStroke[]} getStrokes - Returns the current committed stroke array
 * @property {() => Partial<EnrichedStroke>} getTypeParams - Returns current type-specific params
 * @property {RefObject<DrawCanvasHandle | null>} canvasRef - Ref to the DrawCanvasHandle
 * @property {() => void} onClear - Programmatic clear (no confirm dialog)
 * @property {() => void} onDownload - Triggers JSON download
 * @property {() => void} onDownloadJPG - Triggers JPG download
 * @property {(json: string) => void} onLoadStrokes - Loads a drawing from JSON string
 */
interface UsePaintWindowApiParams {
  setActiveType: (t: DrawStrokeType) => void;
  setColor: (hex: string) => void;
  setOpacity: (v: number) => void;
  setThickness: (px: number) => void;
  setTypeParams: (p: Partial<EnrichedStroke>) => void;
  getActiveType: () => DrawStrokeType;
  getColor: () => string;
  getOpacity: () => number;
  getThickness: () => number;
  getStrokes: () => EnrichedStroke[];
  getTypeParams: () => Partial<EnrichedStroke>;
  canvasRef: RefObject<DrawCanvasHandle | null>;
  onClear: () => void;
  onDownload: () => void;
  onDownloadJPG: () => void;
  onLoadStrokes: (json: string) => void;
}

/**
 * Register window.paintByLanguageModel on mount and clean it up on unmount.
 *
 * Uses refs internally for values read synchronously by API methods (strokes, typeParams)
 * to avoid stale closure issues. State setters are stable React dispatch functions, so
 * they don't need the same treatment.
 *
 * Guards against SSR with a `typeof window !== 'undefined'` check.
 *
 * @param {UsePaintWindowApiParams} params - Setters, getters, and refs from DrawPage
 */
export function usePaintWindowApi({
  setActiveType,
  setColor,
  setOpacity,
  setThickness,
  setTypeParams,
  getActiveType,
  getColor,
  getOpacity,
  getThickness,
  getStrokes,
  getTypeParams,
  canvasRef,
  onClear,
  onDownload,
  onDownloadJPG,
  onLoadStrokes,
}: UsePaintWindowApiParams): void {
  // Keep the latest values of getStrokes/getTypeParams in refs to avoid stale closures
  const getStrokesRef = useRef(getStrokes);
  const getTypeParamsRef = useRef(getTypeParams);
  const getActiveTypeRef = useRef(getActiveType);
  const getColorRef = useRef(getColor);
  const getOpacityRef = useRef(getOpacity);
  const getThicknessRef = useRef(getThickness);
  useEffect(() => { getStrokesRef.current = getStrokes; }, [getStrokes]);
  useEffect(() => { getTypeParamsRef.current = getTypeParams; }, [getTypeParams]);
  useEffect(() => { getActiveTypeRef.current = getActiveType; }, [getActiveType]);
  useEffect(() => { getColorRef.current = getColor; }, [getColor]);
  useEffect(() => { getOpacityRef.current = getOpacity; }, [getOpacity]);
  useEffect(() => { getThicknessRef.current = getThickness; }, [getThickness]);

  // Keep the latest state setters in refs too
  const setActiveTypeRef = useRef(setActiveType);
  const setColorRef = useRef(setColor);
  const setOpacityRef = useRef(setOpacity);
  const setThicknessRef = useRef(setThickness);
  const setTypeParamsRef = useRef(setTypeParams);
  const onClearRef = useRef(onClear);
  const onDownloadRef = useRef(onDownload);
  const onDownloadJPGRef = useRef(onDownloadJPG);
  const onLoadStrokesRef = useRef(onLoadStrokes);

  useEffect(() => { setActiveTypeRef.current = setActiveType; }, [setActiveType]);
  useEffect(() => { setColorRef.current = setColor; }, [setColor]);
  useEffect(() => { setOpacityRef.current = setOpacity; }, [setOpacity]);
  useEffect(() => { setThicknessRef.current = setThickness; }, [setThickness]);
  useEffect(() => { setTypeParamsRef.current = setTypeParams; }, [setTypeParams]);
  useEffect(() => { onClearRef.current = onClear; }, [onClear]);
  useEffect(() => { onDownloadRef.current = onDownload; }, [onDownload]);
  useEffect(() => { onDownloadJPGRef.current = onDownloadJPG; }, [onDownloadJPG]);
  useEffect(() => { onLoadStrokesRef.current = onLoadStrokes; }, [onLoadStrokes]);

  useEffect(() => {
    // Guard against SSR environments
    if (typeof window === 'undefined') return;

    const api: PaintWindowApi = {
      selectStrokeType(type: string) {
        if ((STROKE_TYPES as readonly string[]).includes(type)) {
          setActiveTypeRef.current(type as DrawStrokeType);
        }
      },

      setColor(hex: string) {
        setColorRef.current(hex);
      },

      setOpacity(value: number) {
        setOpacityRef.current(value);
      },

      setThickness(px: number) {
        setThicknessRef.current(px);
      },

      setTypeParam(key: string, value: unknown) {
        const current = getTypeParamsRef.current();
        setTypeParamsRef.current({ ...current, [key]: value });
      },

      click(x: number, y: number) {
        canvasRef.current?.simulateClick(x, y);
      },

      doubleClick(x: number, y: number) {
        canvasRef.current?.simulateDoubleClick(x, y);
      },

      cancelStroke() {
        canvasRef.current?.cancelStroke();
      },

      clearCanvas() {
        onClearRef.current();
      },

      getStrokes() {
        return JSON.parse(JSON.stringify(getStrokesRef.current())) as object[];
      },

      loadStrokes(drawingJson: string) {
        onLoadStrokesRef.current(drawingJson);
      },

      downloadJSON() {
        onDownloadRef.current();
      },

      downloadJPG() {
        onDownloadJPGRef.current();
      },

      getCanvasImageDataUrl() {
        return canvasRef.current?.mainCanvas.toDataURL('image/png') ?? '';
      },

      getState() {
        const strokes = getStrokesRef.current();
        const typeParams = getTypeParamsRef.current();
        return {
          activeType: getActiveTypeRef.current(),
          color: getColorRef.current(),
          opacity: getOpacityRef.current(),
          thickness: getThicknessRef.current(),
          typeParams,
          strokeCount: strokes.length,
        };
      },

      getStrokeTypes() {
        return [...STROKE_TYPES];
      },

      getTypeParamSchema(type: string) {
        if ((STROKE_TYPES as readonly string[]).includes(type)) {
          return { ...STROKE_DEFAULTS[type as DrawStrokeType] };
        }
        return {};
      },
    };

    Object.defineProperty(window, 'paintByLanguageModel', {
      value: api,
      writable: false,
      enumerable: false,
      configurable: true,
    });

    return () => {
      delete (window as unknown as Record<string, unknown>)['paintByLanguageModel'];
    };
  }, [canvasRef]);
}
