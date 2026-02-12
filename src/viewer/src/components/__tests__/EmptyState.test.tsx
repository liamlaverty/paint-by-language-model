/**
 * Unit tests for EmptyState component
 */

import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';
import EmptyState from '@/components/EmptyState';

describe('EmptyState', () => {
  describe('Loading state', () => {
    it('should render loading message when isLoading is true', () => {
      render(<EmptyState isLoading={true} />);

      expect(screen.getByText('Loading artwork...')).toBeInTheDocument();
    });

    it('should render loading icon when isLoading is true', () => {
      render(<EmptyState isLoading={true} />);

      const svg = screen.getByText('Loading artwork...').previousSibling;
      expect(svg).toBeInTheDocument();
      expect(svg?.nodeName).toBe('svg');
    });

    it('should prioritize error over loading when both are true', () => {
      render(<EmptyState isLoading={true} error="Test error" />);

      expect(screen.getByText('Error loading artwork')).toBeInTheDocument();
      expect(screen.queryByText('Loading artwork...')).not.toBeInTheDocument();
    });
  });

  describe('Error state', () => {
    it('should render error message when error prop is provided', () => {
      render(<EmptyState isLoading={false} error="Network connection failed" />);

      expect(screen.getByText('Error loading artwork')).toBeInTheDocument();
      expect(screen.getByText('Network connection failed')).toBeInTheDocument();
    });

    it('should render retry suggestion in error state', () => {
      render(<EmptyState isLoading={false} error="Test error" />);

      expect(screen.getByText('Please try refreshing the page')).toBeInTheDocument();
    });

    it('should render error icon', () => {
      render(<EmptyState isLoading={false} error="Test error" />);

      const svg = screen.getByText('Error loading artwork').previousSibling;
      expect(svg).toBeInTheDocument();
      expect(svg?.nodeName).toBe('svg');
    });

    it('should prioritize error over loading state', () => {
      render(<EmptyState isLoading={true} error="Test error" />);

      expect(screen.getByText('Error loading artwork')).toBeInTheDocument();
      expect(screen.queryByText('Loading artwork...')).not.toBeInTheDocument();
    });
  });

  describe('Default empty state', () => {
    it('should render default message when not loading and no error', () => {
      render(<EmptyState isLoading={false} />);

      expect(screen.getByText('No artwork loaded')).toBeInTheDocument();
    });

    it('should render instruction text in default state', () => {
      render(<EmptyState isLoading={false} />);

      expect(screen.getByText('Select an artwork from the gallery')).toBeInTheDocument();
    });

    it('should render icon in default state', () => {
      render(<EmptyState isLoading={false} />);

      const svg = screen.getByText('No artwork loaded').previousSibling;
      expect(svg).toBeInTheDocument();
      expect(svg?.nodeName).toBe('svg');
    });
  });

  describe('CSS classes', () => {
    it('should apply empty-state class', () => {
      const { container } = render(<EmptyState isLoading={false} />);

      expect(container.querySelector('.empty-state')).toBeInTheDocument();
    });

    it('should apply empty-state class in loading state', () => {
      const { container } = render(<EmptyState isLoading={true} />);

      expect(container.querySelector('.empty-state')).toBeInTheDocument();
    });

    it('should apply empty-state class in error state', () => {
      const { container } = render(<EmptyState isLoading={false} error="Test error" />);

      expect(container.querySelector('.empty-state')).toBeInTheDocument();
    });
  });

  describe('SVG rendering', () => {
    it('should render SVG with correct viewBox in default state', () => {
      const { container } = render(<EmptyState isLoading={false} />);

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('viewBox', '0 0 24 24');
    });

    it('should render SVG with correct viewBox in loading state', () => {
      const { container } = render(<EmptyState isLoading={true} />);

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('viewBox', '0 0 24 24');
    });

    it('should render SVG with correct viewBox in error state', () => {
      const { container } = render(<EmptyState isLoading={false} error="Test" />);

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('viewBox', '0 0 24 24');
    });

    it('should render SVG with stroke attributes', () => {
      const { container } = render(<EmptyState isLoading={false} />);

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('fill', 'none');
      expect(svg).toHaveAttribute('stroke', 'currentColor');
    });
  });

  describe('Edge cases', () => {
    it('should handle empty error string as default state', () => {
      render(<EmptyState isLoading={false} error="" />);

      expect(screen.getByText('No artwork loaded')).toBeInTheDocument();
    });

    it('should handle long error messages', () => {
      const longError = 'A'.repeat(200);
      render(<EmptyState isLoading={false} error={longError} />);

      expect(screen.getByText(longError)).toBeInTheDocument();
    });

    it('should handle special characters in error messages', () => {
      render(<EmptyState isLoading={false} error="Error: <script>alert('xss')</script>" />);

      expect(screen.getByText("Error: <script>alert('xss')</script>")).toBeInTheDocument();
    });
  });

  describe('State transitions', () => {
    it('should switch from loading to default state', () => {
      const { rerender } = render(<EmptyState isLoading={true} />);

      expect(screen.getByText('Loading artwork...')).toBeInTheDocument();

      rerender(<EmptyState isLoading={false} />);

      expect(screen.queryByText('Loading artwork...')).not.toBeInTheDocument();
      expect(screen.getByText('No artwork loaded')).toBeInTheDocument();
    });

    it('should switch from loading to error state', () => {
      const { rerender } = render(<EmptyState isLoading={true} />);

      expect(screen.getByText('Loading artwork...')).toBeInTheDocument();

      rerender(<EmptyState isLoading={false} error="Load failed" />);

      expect(screen.queryByText('Loading artwork...')).not.toBeInTheDocument();
      expect(screen.getByText('Error loading artwork')).toBeInTheDocument();
      expect(screen.getByText('Load failed')).toBeInTheDocument();
    });

    it('should switch from error to default state when error is cleared', () => {
      const { rerender } = render(<EmptyState isLoading={false} error="Test error" />);

      expect(screen.getByText('Error loading artwork')).toBeInTheDocument();

      rerender(<EmptyState isLoading={false} />);

      expect(screen.queryByText('Error loading artwork')).not.toBeInTheDocument();
      expect(screen.getByText('No artwork loaded')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have appropriate ARIA attributes for loading state', () => {
      const { container } = render(<EmptyState isLoading={true} />);

      const emptyState = container.querySelector('.empty-state');
      expect(emptyState).toBeInTheDocument();
    });

    it('should display text content for screen readers', () => {
      render(<EmptyState isLoading={false} />);

      expect(screen.getByText('No artwork loaded')).toBeInTheDocument();
      expect(screen.getByText('Select an artwork from the gallery')).toBeInTheDocument();
    });
  });
});
