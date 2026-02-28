/**
 * Unit tests for SidePanel component
 */

import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SidePanel from '@/components/SidePanel';
import { EnrichedStroke, ArtworkMetadata, EvaluationDetail } from '@/lib/types';

// Mock marked to avoid ESM import issues in Jest
jest.mock('marked', () => ({
  marked: {
    parse: (md: string) => md,
  },
}));

describe('SidePanel', () => {
  const mockMetadata: ArtworkMetadata = {
    artwork_id: 'test-001',
    artist_name: 'Test Artist',
    subject: 'Test Subject',
    canvas_width: 800,
    canvas_height: 600,
    background_color: '#FFFFFF',
    total_strokes: 100,
    total_iterations: 10,
    score_progression: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
  };

  const createLineStroke = (overrides?: Partial<EnrichedStroke>): EnrichedStroke => ({
    index: 5,
    iteration: 2,
    batch_position: 1,
    batch_reasoning: 'Test reasoning for this stroke',
    type: 'line',
    color_hex: '#FF5733',
    thickness: 3,
    opacity: 0.8,
    start_x: 10,
    start_y: 20,
    end_x: 100,
    end_y: 200,
    ...overrides,
  });

  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('Tab bar', () => {
    it('should always render Run Info, Stroke Info, and Report tab buttons', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Run Info')).toBeInTheDocument();
      expect(screen.getByText('Stroke Info')).toBeInTheDocument();
      expect(screen.getByText('Report')).toBeInTheDocument();
    });

    it('should default to Run Info tab when no stroke is selected', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      const runTab = screen.getByText('Run Info');
      expect(runTab).toHaveClass('active');
    });

    it('should auto-switch to Stroke Info tab when stroke is provided', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      const strokeTab = screen.getByText('Stroke Info');
      expect(strokeTab).toHaveClass('active');
    });

    it('should switch to Run Info when clicking Run Info tab', async () => {
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Run Info'));

      expect(screen.getByText('Run Info')).toHaveClass('active');
      expect(screen.getByText('Artist / Style')).toBeInTheDocument();
    });

    it('should switch to Report tab when clicking Report tab', async () => {
      const user = userEvent.setup();
      // Mock fetch for report
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('# Test Report'),
      } as Response);

      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Report'));

      expect(screen.getByText('Report')).toHaveClass('active');
    });

    it('should switch to Stroke Info when clicking Stroke Info tab', async () => {
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Stroke Info'));

      expect(screen.getByText('Stroke Info')).toHaveClass('active');
      expect(screen.getByText(/Hover over a stroke to inspect it/i)).toBeInTheDocument();
    });
  });

  describe('Run Info tab content', () => {
    it('should show artist name and subject', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Test Artist')).toBeInTheDocument();
      expect(screen.getByText('Test Subject')).toBeInTheDocument();
    });

    it('should show canvas size', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Canvas Size')).toBeInTheDocument();
      expect(screen.getByText('800 × 600')).toBeInTheDocument();
    });

    it('should show total iterations and strokes', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Total Iterations')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Total Strokes')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('should show final score with bar', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={{ ...mockMetadata, final_score: 75 }}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Final Score')).toBeInTheDocument();
      expect(screen.getByText('75/100')).toBeInTheDocument();
      const scoreBar = document.querySelector('.run-info .score-bar');
      expect(scoreBar).toHaveStyle({ width: '75%', backgroundColor: '#22c55e' });
    });

    it('should show 0/100 when final_score is not set', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('0/100')).toBeInTheDocument();
    });

    it('should show expanded subject when available', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={{ ...mockMetadata, expanded_subject: 'A detailed expanded subject' }}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Expanded Subject')).toBeInTheDocument();
      expect(screen.getByText('A detailed expanded subject')).toBeInTheDocument();
    });

    it('should not show expanded subject when not available', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.queryByText('Expanded Subject')).not.toBeInTheDocument();
    });

    it('should show formatted generation date when available', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={{ ...mockMetadata, generation_date: '2025-06-15T12:00:00Z' }}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByText('15/06/2025')).toBeInTheDocument();
    });

    it('should not show date row when generation_date is not set', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.queryByText('Date')).not.toBeInTheDocument();
    });

    it('should not render stroke metadata when Run Info tab is active', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.queryByText('Identity')).not.toBeInTheDocument();
      expect(screen.queryByText('Appearance')).not.toBeInTheDocument();
    });
  });

  describe('Stroke Info tab — hover hint (no stroke)', () => {
    it('should render hover hint on Stroke Info tab when no stroke selected', async () => {
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Stroke Info'));

      expect(screen.getByText(/Hover over a stroke to inspect it/i)).toBeInTheDocument();
      expect(screen.getByText(/Click a stroke to lock its metadata/i)).toBeInTheDocument();
    });
  });

  describe('Stroke selected state', () => {
    it('should render stroke header with correct index', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ index: 5 })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText(/Stroke 6 of 100/i)).toBeInTheDocument();
    });

    it('should render Identity section', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Identity')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('line')).toBeInTheDocument();
      expect(screen.getByText('Iteration')).toBeInTheDocument();
      expect(screen.getByText('3 of 10')).toBeInTheDocument();
      expect(screen.getByText('Batch Position')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });

    it('should render Appearance section', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Appearance')).toBeInTheDocument();
      expect(screen.getByText('Color')).toBeInTheDocument();
      expect(screen.getByText('#FF5733')).toBeInTheDocument();
      expect(screen.getByText('Opacity')).toBeInTheDocument();
      expect(screen.getByText('80%')).toBeInTheDocument();
      expect(screen.getByText('Thickness')).toBeInTheDocument();
      expect(screen.getByText('3px')).toBeInTheDocument();
    });

    it('should render batch reasoning', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Batch Reasoning')).toBeInTheDocument();
      expect(screen.getByText('Test reasoning for this stroke')).toBeInTheDocument();
    });

    it('should render score section with correct value', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 5 })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Score at Iteration')).toBeInTheDocument();
      expect(screen.getByText('50/100')).toBeInTheDocument();
    });
  });

  describe('Locked state', () => {
    it('should show locked badge when isLocked is true', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={true}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Locked')).toBeInTheDocument();
    });

    it('should not show locked badge when isLocked is false', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.queryByText('Locked')).not.toBeInTheDocument();
    });

    it('should show Clear Selection button when locked with stroke', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={true}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Clear Selection')).toBeInTheDocument();
    });

    it('should not show Clear Selection button when not locked', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.queryByText('Clear Selection')).not.toBeInTheDocument();
    });

    it('should not show Clear Selection button when locked but no stroke', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={true}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.queryByText('Clear Selection')).not.toBeInTheDocument();
    });

    it('should call onClearSelection when button is clicked', async () => {
      const onClearSelection = jest.fn();
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={true}
          onClearSelection={onClearSelection}
        />
      );

      await user.click(screen.getByText('Clear Selection'));

      expect(onClearSelection).toHaveBeenCalledTimes(1);
    });
  });

  describe('Line stroke geometry', () => {
    it('should render line geometry section', () => {
      render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Geometry')).toBeInTheDocument();
      expect(screen.getByText('Start')).toBeInTheDocument();
      expect(screen.getByText('(10, 20)')).toBeInTheDocument();
      expect(screen.getByText('End')).toBeInTheDocument();
      expect(screen.getByText('(100, 200)')).toBeInTheDocument();
    });
  });

  describe('Arc stroke geometry', () => {
    const arcStroke: EnrichedStroke = {
      index: 0,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'Arc test',
      type: 'arc',
      color_hex: '#000000',
      thickness: 2,
      opacity: 1.0,
      arc_bbox: [10, 20, 100, 200],
      arc_start_angle: 0,
      arc_end_angle: 180,
    };

    it('should render arc geometry section', () => {
      render(
        <SidePanel
          stroke={arcStroke}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Bbox')).toBeInTheDocument();
      expect(screen.getByText('[10, 20, 100, 200]')).toBeInTheDocument();
      expect(screen.getByText('Angles')).toBeInTheDocument();
      expect(screen.getByText('0° → 180°')).toBeInTheDocument();
    });
  });

  describe('Polyline stroke geometry', () => {
    const polylineStroke: EnrichedStroke = {
      index: 0,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'Polyline test',
      type: 'polyline',
      color_hex: '#000000',
      thickness: 2,
      opacity: 1.0,
      points: [
        [10, 20],
        [30, 40],
        [50, 60],
        [70, 80],
        [90, 100],
        [110, 120],
      ],
    };

    it('should render polyline geometry section', () => {
      render(
        <SidePanel
          stroke={polylineStroke}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Point Count')).toBeInTheDocument();
      expect(screen.getByText('6')).toBeInTheDocument();
      expect(screen.getByText('Path')).toBeInTheDocument();
    });

    it('should truncate polyline path preview after 4 points', () => {
      render(
        <SidePanel
          stroke={polylineStroke}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText(/\(10,20\) \(30,40\) \(50,60\) \(70,80\) …/)).toBeInTheDocument();
    });
  });

  describe('Circle stroke geometry', () => {
    const circleStroke: EnrichedStroke = {
      index: 0,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'Circle test',
      type: 'circle',
      color_hex: '#000000',
      thickness: 2,
      opacity: 1.0,
      center_x: 50,
      center_y: 75,
      radius: 25,
      fill: true,
    };

    it('should render circle geometry section', () => {
      render(
        <SidePanel
          stroke={circleStroke}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Center')).toBeInTheDocument();
      expect(screen.getByText('(50, 75)')).toBeInTheDocument();
      expect(screen.getByText('Radius')).toBeInTheDocument();
      expect(screen.getByText('25px')).toBeInTheDocument();
      expect(screen.getByText('Fill')).toBeInTheDocument();
      expect(screen.getByText('Solid')).toBeInTheDocument();
    });

    it('should show Outline for unfilled circle', () => {
      render(
        <SidePanel
          stroke={{ ...circleStroke, fill: false }}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Outline')).toBeInTheDocument();
    });
  });

  describe('Splatter stroke geometry', () => {
    const splatterStroke: EnrichedStroke = {
      index: 0,
      iteration: 0,
      batch_position: 0,
      batch_reasoning: 'Splatter test',
      type: 'splatter',
      color_hex: '#000000',
      thickness: 2,
      opacity: 1.0,
      center_x: 100,
      center_y: 150,
      splatter_radius: 30,
      splatter_count: 20,
      dot_size_min: 1,
      dot_size_max: 5,
    };

    it('should render splatter geometry section', () => {
      render(
        <SidePanel
          stroke={splatterStroke}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Center')).toBeInTheDocument();
      expect(screen.getByText('(100, 150)')).toBeInTheDocument();
      expect(screen.getByText('Radius')).toBeInTheDocument();
      expect(screen.getByText('30px')).toBeInTheDocument();
      expect(screen.getByText('Dot Count')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
      expect(screen.getByText('Dot Size Range')).toBeInTheDocument();
      expect(screen.getByText('1–5px')).toBeInTheDocument();
    });
  });

  describe('Score bar colors', () => {
    it('should use red color for score < 40', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 1 })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      const scoreBars = document.querySelectorAll('.score-bar');
      // Stroke Info tab is active; only one .score-bar is rendered
      const scoreBar = scoreBars[0];
      expect(scoreBar).toHaveStyle({ backgroundColor: '#ef4444' });
    });

    it('should use yellow color for score 40-69', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 5 })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      const scoreBar = document.querySelector('.score-bar');
      expect(scoreBar).toHaveStyle({ backgroundColor: '#f59e0b' });
    });

    it('should use green color for score >= 70', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 8 })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      const scoreBar = document.querySelector('.score-bar');
      expect(scoreBar).toHaveStyle({ backgroundColor: '#22c55e' });
    });

    it('should set correct width for score bar', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 5 })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      const scoreBar = document.querySelector('.score-bar');
      expect(scoreBar).toHaveStyle({ width: '50%' });
    });
  });

  describe('Color swatch', () => {
    it('should render color swatch with correct background color', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ color_hex: '#FF5733' })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      const swatch = document.querySelector('.color-swatch');
      expect(swatch).toHaveStyle({ backgroundColor: '#FF5733' });
    });
  });

  describe('Opacity formatting', () => {
    it('should display opacity as percentage', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ opacity: 0.5 })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should round opacity to nearest integer', () => {
      render(
        <SidePanel
          stroke={createLineStroke({ opacity: 0.756 })}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('76%')).toBeInTheDocument();
    });
  });

  describe('Report tab', () => {
    it('should fetch and render markdown when Report tab is clicked', async () => {
      const user = userEvent.setup();
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('# Generation Report\n\nThis is a **test** report.'),
      } as Response);

      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Report'));

      // Wait for the markdown to be rendered (marked mock returns raw markdown)
      const reportContainer = await screen.findByText(/Generation Report/);
      expect(reportContainer).toBeInTheDocument();
      expect(screen.getByText(/This is a/)).toBeInTheDocument();
    });

    it('should show empty message when report fetch fails', async () => {
      const user = userEvent.setup();
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: () => Promise.resolve(''),
      } as Response);

      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Report'));

      const emptyMsg = await screen.findByText('No report available for this artwork.');
      expect(emptyMsg).toBeInTheDocument();
    });

    it('should show empty message when fetch rejects', async () => {
      const user = userEvent.setup();
      global.fetch = jest.fn().mockRejectedValueOnce(new Error('Network error'));

      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Report'));

      const emptyMsg = await screen.findByText('No report available for this artwork.');
      expect(emptyMsg).toBeInTheDocument();
    });

    it('should construct fetch URL using artwork_id from metadata', async () => {
      const user = userEvent.setup();
      const fetchSpy = jest.fn().mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('# Report'),
      } as Response);
      global.fetch = fetchSpy;

      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Report'));

      expect(fetchSpy).toHaveBeenCalledWith('/data/test-001/generation_report.md');
    });

    it('should only fetch report once (cached in state)', async () => {
      const user = userEvent.setup();
      const fetchSpy = jest.fn().mockResolvedValue({
        ok: true,
        text: () => Promise.resolve('# Report'),
      } as Response);
      global.fetch = fetchSpy;

      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      await user.click(screen.getByText('Report'));
      await screen.findByText('Report');

      // Switch away and back
      await user.click(screen.getByText('Run Info'));
      await user.click(screen.getByText('Report'));

      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('Auto-switch behavior', () => {
    it('should auto-switch to Stroke Info when stroke transitions from null to non-null', () => {
      const { rerender } = render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Run Info')).toHaveClass('active');

      rerender(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Stroke Info')).toHaveClass('active');
      expect(screen.getByText('Identity')).toBeInTheDocument();
    });

    it('should auto-switch to Run Info when stroke transitions from non-null to null', () => {
      const { rerender } = render(
        <SidePanel
          stroke={createLineStroke()}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Stroke Info')).toHaveClass('active');

      rerender(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText('Run Info')).toHaveClass('active');
      expect(screen.getByText('Artist / Style')).toBeInTheDocument();
    });
  });

  describe('Evaluation Feedback section', () => {
    const mockEvaluations: EvaluationDetail[] = [
      {
        iteration: 2,
        score: 72,
        feedback: 'The composition shows good understanding of the style.',
        strengths: 'Strong use of line weight and tonal variation.',
        suggestions: 'Consider adding more gestural marks in the background.',
      },
    ];

    it('renders "Evaluation Feedback" heading when evaluation exists for stroke iteration', async () => {
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 2 })}
          metadata={mockMetadata}
          evaluations={mockEvaluations}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );
      await user.click(screen.getByText('Stroke Info'));
      expect(screen.getByText('Evaluation Feedback')).toBeInTheDocument();
    });

    it('renders feedback, strengths, and suggestions in reasoning-box elements', async () => {
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 2 })}
          metadata={mockMetadata}
          evaluations={mockEvaluations}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );
      await user.click(screen.getByText('Stroke Info'));
      expect(
        screen.getByText('The composition shows good understanding of the style.')
      ).toBeInTheDocument();
      expect(
        screen.getByText('Strong use of line weight and tonal variation.')
      ).toBeInTheDocument();
      expect(
        screen.getByText('Consider adding more gestural marks in the background.')
      ).toBeInTheDocument();
    });

    it('does not render evaluation section when evaluations prop is empty', async () => {
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 2 })}
          metadata={mockMetadata}
          evaluations={[]}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );
      await user.click(screen.getByText('Stroke Info'));
      expect(screen.queryByText('Evaluation Feedback')).not.toBeInTheDocument();
    });

    it('does not render evaluation section when no evaluation matches stroke iteration', async () => {
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 5 })}
          metadata={mockMetadata}
          evaluations={mockEvaluations}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );
      await user.click(screen.getByText('Stroke Info'));
      expect(screen.queryByText('Evaluation Feedback')).not.toBeInTheDocument();
    });

    it('hides sub-boxes for empty feedback, strengths, and suggestions', async () => {
      const user = userEvent.setup();
      const sparseEvaluations: EvaluationDetail[] = [
        {
          iteration: 2,
          score: 50,
          feedback: '',
          strengths: '',
          suggestions: '',
        },
      ];
      render(
        <SidePanel
          stroke={createLineStroke({ iteration: 2 })}
          metadata={mockMetadata}
          evaluations={sparseEvaluations}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );
      await user.click(screen.getByText('Stroke Info'));
      // heading still renders because the evaluation object exists
      expect(screen.getByText('Evaluation Feedback')).toBeInTheDocument();
      // but individual sub-labels are hidden when fields are empty
      expect(screen.queryByText('Feedback')).not.toBeInTheDocument();
      expect(screen.queryByText('Strengths')).not.toBeInTheDocument();
      expect(screen.queryByText('Suggestions')).not.toBeInTheDocument();
    });

    it('does not render evaluation section when no stroke is selected', async () => {
      const user = userEvent.setup();
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          evaluations={mockEvaluations}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );
      await user.click(screen.getByText('Stroke Info'));
      expect(screen.queryByText('Evaluation Feedback')).not.toBeInTheDocument();
    });
  });
});
