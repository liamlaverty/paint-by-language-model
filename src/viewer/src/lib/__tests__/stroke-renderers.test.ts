/**
 * Unit tests for stroke-renderers.ts - Canvas rendering functions
 */

import { renderStroke } from '@/lib/renderers';
import type { EnrichedStroke } from '@/lib/types';

// Mock canvas context
const createMockContext = () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];

  const mockGradient = {
    addColorStop: jest.fn(),
  };

  const ctx = {
    canvas: { width: 800, height: 600 },
    save: jest.fn(() => calls.push({ method: 'save', args: [] })),
    restore: jest.fn(() => calls.push({ method: 'restore', args: [] })),
    beginPath: jest.fn(() => calls.push({ method: 'beginPath', args: [] })),
    moveTo: jest.fn((...args) => calls.push({ method: 'moveTo', args })),
    lineTo: jest.fn((...args) => calls.push({ method: 'lineTo', args })),
    stroke: jest.fn(() => calls.push({ method: 'stroke', args: [] })),
    fill: jest.fn(() => calls.push({ method: 'fill', args: [] })),
    arc: jest.fn((...args) => calls.push({ method: 'arc', args })),
    ellipse: jest.fn((...args) => calls.push({ method: 'ellipse', args })),
    createRadialGradient: jest.fn(() => mockGradient),
    strokeStyle: '',
    fillStyle: '',
    lineWidth: 1,
    lineCap: 'butt' as CanvasLineCap,
    lineJoin: 'miter' as CanvasLineJoin,
    globalAlpha: 1,
    getCalls: () => calls,
    clearCalls: () => calls.splice(0, calls.length),
  } as unknown as CanvasRenderingContext2D & {
    getCalls: () => Array<{ method: string; args: unknown[] }>;
    clearCalls: () => void;
  };

  return ctx;
};

describe('renderStroke', () => {
  it('should call save and restore for each stroke', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 0,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'line',
      color_hex: '#FF0000',
      thickness: 2,
      opacity: 1.0,
      start_x: 10,
      start_y: 20,
      end_x: 100,
      end_y: 200,
    };

    renderStroke(ctx, stroke, 0, false);

    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
  });

  it('should render line stroke correctly', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 0,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'line',
      color_hex: '#FF5733',
      thickness: 3,
      opacity: 0.8,
      start_x: 50,
      start_y: 60,
      end_x: 150,
      end_y: 160,
    };

    renderStroke(ctx, stroke, 0, false);

    expect(ctx.beginPath).toHaveBeenCalled();
    expect(ctx.moveTo).toHaveBeenCalledWith(50, 60);
    expect(ctx.lineTo).toHaveBeenCalledWith(150, 160);
    expect(ctx.strokeStyle).toBe('rgba(255,87,51,0.8)');
    expect(ctx.lineWidth).toBe(3);
    expect(ctx.lineCap).toBe('butt');
    expect(ctx.stroke).toHaveBeenCalled();
  });

  it('should render line stroke in hit mode with unique color', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 5,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'line',
      color_hex: '#FF5733',
      thickness: 2,
      opacity: 0.5,
      start_x: 50,
      start_y: 60,
      end_x: 150,
      end_y: 160,
    };

    renderStroke(ctx, stroke, 5, true);

    expect(ctx.strokeStyle).toBe('rgb(0,0,6)'); // index 5 + 1 = 6
    expect(ctx.lineWidth).toBe(4); // Hit mode uses max(thickness, 4)
  });

  it('should render arc stroke correctly', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 1,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'arc',
      color_hex: '#00FF00',
      thickness: 2,
      opacity: 1.0,
      arc_bbox: [50, 50, 150, 100],
      arc_start_angle: 0,
      arc_end_angle: 180,
    };

    renderStroke(ctx, stroke, 1, false);

    expect(ctx.beginPath).toHaveBeenCalled();
    expect(ctx.ellipse).toHaveBeenCalledWith(
      100, // cx = (50 + 150) / 2
      75, // cy = (50 + 100) / 2
      50, // rx = (150 - 50) / 2
      25, // ry = (100 - 50) / 2
      0,
      0, // 0 degrees in radians
      Math.PI, // 180 degrees in radians
      false
    );
    expect(ctx.stroke).toHaveBeenCalled();
  });

  it('should render polyline stroke correctly', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 2,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'polyline',
      color_hex: '#0000FF',
      thickness: 4,
      opacity: 0.9,
      points: [
        [10, 20],
        [30, 40],
        [50, 30],
        [70, 50],
      ],
    };

    renderStroke(ctx, stroke, 2, false);

    expect(ctx.beginPath).toHaveBeenCalled();
    expect(ctx.moveTo).toHaveBeenCalledWith(10, 20);
    expect(ctx.lineTo).toHaveBeenCalledWith(30, 40);
    expect(ctx.lineTo).toHaveBeenCalledWith(50, 30);
    expect(ctx.lineTo).toHaveBeenCalledWith(70, 50);
    expect(ctx.lineJoin).toBe('round');
    expect(ctx.lineCap).toBe('round');
    expect(ctx.stroke).toHaveBeenCalled();
  });

  it('should skip polyline with less than 2 points', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 3,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'polyline',
      color_hex: '#0000FF',
      thickness: 2,
      opacity: 1.0,
      points: [[10, 20]], // Only 1 point
    };

    renderStroke(ctx, stroke, 3, false);

    // Should call save/restore but not render
    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
    expect(ctx.beginPath).not.toHaveBeenCalled();
  });

  it('should render filled circle stroke correctly', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 4,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'circle',
      color_hex: '#FFFF00',
      thickness: 2,
      opacity: 0.7,
      center_x: 100,
      center_y: 150,
      radius: 50,
      fill: true,
    };

    renderStroke(ctx, stroke, 4, false);

    expect(ctx.beginPath).toHaveBeenCalled();
    expect(ctx.arc).toHaveBeenCalledWith(100, 150, 50, 0, Math.PI * 2);
    expect(ctx.fillStyle).toBe('rgba(255,255,0,0.7)');
    expect(ctx.fill).toHaveBeenCalled();
    expect(ctx.stroke).not.toHaveBeenCalled();
  });

  it('should render outlined circle stroke correctly', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 5,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'circle',
      color_hex: '#FF00FF',
      thickness: 3,
      opacity: 1.0,
      center_x: 200,
      center_y: 250,
      radius: 30,
      fill: false,
    };

    renderStroke(ctx, stroke, 5, false);

    expect(ctx.beginPath).toHaveBeenCalled();
    expect(ctx.arc).toHaveBeenCalledWith(200, 250, 30, 0, Math.PI * 2);
    expect(ctx.strokeStyle).toBe('rgba(255,0,255,1)');
    expect(ctx.lineWidth).toBe(3);
    expect(ctx.stroke).toHaveBeenCalled();
    expect(ctx.fill).not.toHaveBeenCalled();
  });

  it('should render splatter stroke with deterministic dots', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 6,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'splatter',
      color_hex: '#00FFFF',
      thickness: 1,
      opacity: 0.6,
      center_x: 400,
      center_y: 300,
      splatter_count: 50,
      splatter_radius: 100,
      dot_size_min: 1,
      dot_size_max: 5,
    };

    renderStroke(ctx, stroke, 6, false);

    // Should call arc for each dot (some may be skipped if outside bounds)
    // At minimum, many dots should be rendered
    const calls = (ctx as any).getCalls();
    const arcCalls = calls.filter((c: any) => c.method === 'arc');

    expect(arcCalls.length).toBeGreaterThan(0);
    expect(arcCalls.length).toBeLessThanOrEqual(stroke.splatter_count!);
  });

  it('should render splatter with same seed consistently', () => {
    const ctx1 = createMockContext();
    const ctx2 = createMockContext();

    const stroke: EnrichedStroke = {
      index: 10,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'splatter',
      color_hex: '#FFFFFF',
      thickness: 1,
      opacity: 1.0,
      center_x: 400,
      center_y: 300,
      splatter_count: 20,
      splatter_radius: 50,
      dot_size_min: 2,
      dot_size_max: 4,
    };

    renderStroke(ctx1, stroke, 10, false);
    renderStroke(ctx2, stroke, 10, false);

    const calls1 = (ctx1 as any).getCalls();
    const calls2 = (ctx2 as any).getCalls();

    // Should produce identical rendering calls
    expect(calls1).toEqual(calls2);
  });

  it('should render dry-brush stroke correctly', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 11,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'dry-brush',
      color_hex: '#8B4513',
      thickness: 10,
      opacity: 0.8,
      points: [
        [100, 100],
        [200, 150],
        [300, 120],
      ],
      brush_width: 20,
      bristle_count: 10,
      gap_probability: 0.3,
    };

    renderStroke(ctx, stroke, 11, false);

    expect(ctx.beginPath).toHaveBeenCalled();
    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
  });

  it('should render chalk stroke correctly', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 12,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'chalk',
      color_hex: '#FFFFFF',
      thickness: 5,
      opacity: 0.7,
      points: [
        [100, 100],
        [200, 150],
        [300, 120],
      ],
      chalk_width: 20,
      grain_density: 4,
    };

    renderStroke(ctx, stroke, 12, false);

    // Should call fill for dots (grain_density dots per sample point)
    expect(ctx.fill).toHaveBeenCalled();
    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
  });

  it('should render wet-brush stroke without throwing', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 13,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'wet-brush',
      color_hex: '#4477AA',
      thickness: 10,
      opacity: 0.7,
      softness: 5,
      flow: 0.8,
      points: [
        [100, 100],
        [200, 200],
        [300, 150],
      ],
    };

    // Should not throw
    expect(() => renderStroke(ctx, stroke, 13, false)).not.toThrow();

    // beginPath should be called (polyline path)
    expect(ctx.beginPath).toHaveBeenCalled();
    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
  });

  it('should render wet-brush in hit mode without throwing', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 14,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'wet-brush',
      color_hex: '#AA4477',
      thickness: 8,
      opacity: 0.9,
      softness: 4,
      flow: 1.0,
      points: [
        [50, 50],
        [150, 100],
      ],
    };

    expect(() => renderStroke(ctx, stroke, 14, true)).not.toThrow();
    expect(ctx.beginPath).toHaveBeenCalled();
  });

  it('should render burn stroke without throwing', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 15,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'burn',
      color_hex: '#000000',
      thickness: 1,
      opacity: 1.0,
      center_x: 200,
      center_y: 150,
      radius: 60,
      intensity: 0.5,
    };

    expect(() => renderStroke(ctx, stroke, 15, false)).not.toThrow();

    // fill should be called (gradient circle)
    expect(ctx.fill).toHaveBeenCalled();
    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
  });

  it('should set multiply compositing for burn stroke visual rendering', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 16,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'burn',
      color_hex: '#000000',
      thickness: 1,
      opacity: 1.0,
      center_x: 100,
      center_y: 100,
      radius: 40,
      intensity: 0.6,
    };

    renderStroke(ctx, stroke, 16, false);

    expect(ctx.globalCompositeOperation).toBe('multiply');
  });

  it('should render burn stroke in hit mode without throwing', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 17,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'burn',
      color_hex: '#000000',
      thickness: 1,
      opacity: 1.0,
      center_x: 150,
      center_y: 120,
      radius: 50,
      intensity: 0.4,
    };

    expect(() => renderStroke(ctx, stroke, 17, true)).not.toThrow();
    expect(ctx.fill).toHaveBeenCalled();
  });

  it('should render dodge stroke without throwing', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 18,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'dodge',
      color_hex: '#ffffff',
      thickness: 1,
      opacity: 1.0,
      center_x: 200,
      center_y: 150,
      radius: 60,
      intensity: 0.5,
    };

    expect(() => renderStroke(ctx, stroke, 18, false)).not.toThrow();

    // fill should be called (gradient circle)
    expect(ctx.fill).toHaveBeenCalled();
    expect(ctx.save).toHaveBeenCalled();
    expect(ctx.restore).toHaveBeenCalled();
  });

  it('should set screen compositing for dodge stroke visual rendering', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 19,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'dodge',
      color_hex: '#ffffff',
      thickness: 1,
      opacity: 1.0,
      center_x: 100,
      center_y: 100,
      radius: 40,
      intensity: 0.6,
    };

    renderStroke(ctx, stroke, 19, false);

    expect(ctx.globalCompositeOperation).toBe('screen');
  });

  it('should render dodge stroke in hit mode without throwing', () => {
    const ctx = createMockContext();
    const stroke: EnrichedStroke = {
      index: 20,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'test',
      type: 'dodge',
      color_hex: '#ffffff',
      thickness: 1,
      opacity: 1.0,
      center_x: 150,
      center_y: 120,
      radius: 50,
      intensity: 0.4,
    };

    expect(() => renderStroke(ctx, stroke, 20, true)).not.toThrow();
    expect(ctx.fill).toHaveBeenCalled();
  });
});
