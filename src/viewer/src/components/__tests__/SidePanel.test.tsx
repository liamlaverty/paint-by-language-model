/**
 * Unit tests for SidePanel component
 */

import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SidePanel from '@/components/SidePanel';
import { EnrichedStroke, ArtworkMetadata } from '@/lib/types';

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

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Empty state (no stroke selected)', () => {
    it('should render artwork header when no stroke is selected', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText(/Test Artist.*test-001/)).toBeInTheDocument();
      expect(screen.getByText('Test Subject')).toBeInTheDocument();
    });

    it('should render hover hint when no stroke is selected', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.getByText(/Hover over a stroke to inspect it/i)).toBeInTheDocument();
      expect(screen.getByText(/Click a stroke to lock its metadata/i)).toBeInTheDocument();
    });

    it('should not render stroke metadata when no stroke is selected', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={false}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.queryByText(/Identity/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Appearance/i)).not.toBeInTheDocument();
    });

    it('should not render Clear Selection button when no stroke is selected', () => {
      render(
        <SidePanel
          stroke={null}
          metadata={mockMetadata}
          isLocked={true}
          onClearSelection={jest.fn()}
        />
      );

      expect(screen.queryByText(/Clear Selection/i)).not.toBeInTheDocument();
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

    it('should show Clear Selection button when locked', () => {
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

      const scoreBar = document.querySelector('.score-bar');
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
});
