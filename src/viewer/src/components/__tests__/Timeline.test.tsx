/**
 * Unit tests for Timeline component
 */

import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Timeline from '@/components/Timeline';

describe('Timeline', () => {
  const defaultProps = {
    current: 42,
    total: 100,
    onChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render scrubber with correct values', () => {
      render(<Timeline {...defaultProps} />);

      const slider = screen.getByRole('slider');
      expect(slider).toBeInTheDocument();
      expect(slider).toHaveAttribute('min', '0');
      expect(slider).toHaveAttribute('max', '100');
      expect(slider).toHaveValue('42');
    });

    it('should render position label', () => {
      render(<Timeline {...defaultProps} />);

      expect(screen.getByText('42 / 100')).toBeInTheDocument();
    });

    it('should apply monospace font to label', () => {
      render(<Timeline {...defaultProps} />);

      const label = screen.getByText('42 / 100');
      expect(label).toHaveStyle({ fontFamily: 'var(--font-mono)' });
    });

    it('should apply min-width to label', () => {
      render(<Timeline {...defaultProps} />);

      const label = screen.getByText('42 / 100');
      expect(label).toHaveStyle({ minWidth: '90px' });
    });
  });

  describe('Hidden state', () => {
    it('should return null when total is 0', () => {
      const { container } = render(<Timeline {...defaultProps} total={0} />);

      expect(container.firstChild).toBeNull();
    });

    it('should not render when no data is loaded', () => {
      render(<Timeline current={0} total={0} onChange={jest.fn()} />);

      expect(screen.queryByRole('slider')).not.toBeInTheDocument();
    });
  });

  describe('Position display', () => {
    it('should display current position at start', () => {
      render(<Timeline current={0} total={50} onChange={jest.fn()} />);

      expect(screen.getByText('0 / 50')).toBeInTheDocument();
    });

    it('should display current position at end', () => {
      render(<Timeline current={50} total={50} onChange={jest.fn()} />);

      expect(screen.getByText('50 / 50')).toBeInTheDocument();
    });

    it('should display current position in middle', () => {
      render(<Timeline current={25} total={50} onChange={jest.fn()} />);

      expect(screen.getByText('25 / 50')).toBeInTheDocument();
    });

    it('should handle large numbers correctly', () => {
      render(<Timeline current={999} total={1000} onChange={jest.fn()} />);

      expect(screen.getByText('999 / 1000')).toBeInTheDocument();
    });
  });

  describe('Slider interactions', () => {
    it('should call onChange with new value when slider changes', () => {
      const onChange = jest.fn();
      render(<Timeline current={10} total={100} onChange={onChange} />);

      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '75' } });

      expect(onChange).toHaveBeenCalledWith(75);
    });

    it('should update when current prop changes', () => {
      const { rerender } = render(<Timeline {...defaultProps} current={10} />);

      expect(screen.getByRole('slider')).toHaveValue('10');

      rerender(<Timeline {...defaultProps} current={50} />);

      expect(screen.getByRole('slider')).toHaveValue('50');
    });

    it('should update label when current prop changes', () => {
      const { rerender } = render(<Timeline {...defaultProps} current={10} />);

      expect(screen.getByText('10 / 100')).toBeInTheDocument();

      rerender(<Timeline {...defaultProps} current={75} />);

      expect(screen.getByText('75 / 100')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have title attribute on slider', () => {
      render(<Timeline {...defaultProps} />);

      const slider = screen.getByRole('slider');
      expect(slider).toHaveAttribute('title', 'Stroke 42 of 100');
    });

    it('should update title when position changes', () => {
      const { rerender } = render(<Timeline {...defaultProps} current={10} />);

      expect(screen.getByRole('slider')).toHaveAttribute('title', 'Stroke 10 of 100');

      rerender(<Timeline {...defaultProps} current={90} />);

      expect(screen.getByRole('slider')).toHaveAttribute('title', 'Stroke 90 of 100');
    });
  });

  describe('Edge cases', () => {
    it('should handle total of 1', () => {
      render(<Timeline current={0} total={1} onChange={jest.fn()} />);

      expect(screen.getByText('0 / 1')).toBeInTheDocument();
      expect(screen.getByRole('slider')).toHaveAttribute('max', '1');
    });

    it('should handle current equal to total', () => {
      render(<Timeline current={100} total={100} onChange={jest.fn()} />);

      expect(screen.getByText('100 / 100')).toBeInTheDocument();
      expect(screen.getByRole('slider')).toHaveValue('100');
    });
  });

  describe('CSS classes', () => {
    it('should apply timeline class to container', () => {
      const { container } = render(<Timeline {...defaultProps} />);

      expect(container.firstChild).toHaveClass('timeline');
    });

    it('should apply timeline-label class to label', () => {
      render(<Timeline {...defaultProps} />);

      const label = screen.getByText('42 / 100');
      expect(label).toHaveClass('timeline-label');
    });
  });
});
