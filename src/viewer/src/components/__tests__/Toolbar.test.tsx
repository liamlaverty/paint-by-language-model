/**
 * Unit tests for Toolbar component
 */

import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Toolbar from '@/components/Toolbar';

describe('Toolbar', () => {
  const defaultProps = {
    onReset: jest.fn(),
    onPlay: jest.fn(),
    onPause: jest.fn(),
    onStepBackward: jest.fn(),
    onStepForward: jest.fn(),
    onShowAll: jest.fn(),
    isPlaying: false,
    isLoaded: true,
    speed: 50,
    onSpeedChange: jest.fn(),
    infoText: 'test-artwork · 42/70 strokes',
    highlightEnabled: false,
    onToggleHighlight: jest.fn(),
    onCopyUrl: jest.fn(),
    onDownloadJSON: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render all control buttons', () => {
      render(<Toolbar {...defaultProps} />);

      expect(screen.getByText('⏮ Reset')).toBeInTheDocument();
      expect(screen.getByText('▶️ Play')).toBeInTheDocument();
      expect(screen.getByText('⏮ Step Back')).toBeInTheDocument();
      expect(screen.getByText('⏭ Step Forward')).toBeInTheDocument();
      expect(screen.getByText('⏩ Fin')).toBeInTheDocument();
    });

    it('should render speed slider with correct value', () => {
      render(<Toolbar {...defaultProps} />);

      const slider = screen.getByRole('slider', { name: /speed/i });
      expect(slider).toHaveValue('50');
    });

    it('should display info text', () => {
      render(<Toolbar {...defaultProps} />);

      expect(screen.getByText('test-artwork · 42/70 strokes')).toBeInTheDocument();
    });
  });

  describe('Play/Pause toggle', () => {
    it('should show Play button when not playing', () => {
      render(<Toolbar {...defaultProps} isPlaying={false} />);

      expect(screen.getByText('▶️ Play')).toBeInTheDocument();
      expect(screen.queryByText('⏸️ Pause')).not.toBeInTheDocument();
    });

    it('should show Pause button when playing', () => {
      render(<Toolbar {...defaultProps} isPlaying={true} />);

      expect(screen.getByText('⏸️ Pause')).toBeInTheDocument();
      expect(screen.queryByText('▶️ Play')).not.toBeInTheDocument();
    });
  });

  describe('Button disabled states', () => {
    it('should disable all buttons except Home when isLoaded is false', () => {
      render(<Toolbar {...defaultProps} isLoaded={false} />);

      expect(screen.getByText('⏮ Reset')).toBeDisabled();
      expect(screen.getByText('▶️ Play')).toBeDisabled();
      expect(screen.getByText('⏮ Step Back')).toBeDisabled();
      expect(screen.getByText('⏭ Step Forward')).toBeDisabled();
      expect(screen.getByText('⏩ Fin')).toBeDisabled();
      expect(screen.getByRole('slider')).toBeDisabled();
    });

    it('should disable Reset, Step Back, Step Forward, and Fin when playing', () => {
      render(<Toolbar {...defaultProps} isPlaying={true} />);

      expect(screen.getByText('⏮ Reset')).toBeDisabled();
      expect(screen.getByText('⏮ Step Back')).toBeDisabled();
      expect(screen.getByText('⏭ Step Forward')).toBeDisabled();
      expect(screen.getByText('⏩ Fin')).toBeDisabled();
      expect(screen.getByText('⏸️ Pause')).not.toBeDisabled();
    });

    it('should enable all playback buttons when loaded and not playing', () => {
      render(<Toolbar {...defaultProps} isLoaded={true} isPlaying={false} />);

      expect(screen.getByText('⏮ Reset')).not.toBeDisabled();
      expect(screen.getByText('▶️ Play')).not.toBeDisabled();
      expect(screen.getByText('⏮ Step Back')).not.toBeDisabled();
      expect(screen.getByText('⏭ Step Forward')).not.toBeDisabled();
      expect(screen.getByText('⏩ Fin')).not.toBeDisabled();
    });
  });

  describe('Button interactions', () => {
    it('should call onReset when Reset button is clicked', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} />);

      await user.click(screen.getByText('⏮ Reset'));

      expect(defaultProps.onReset).toHaveBeenCalledTimes(1);
    });

    it('should call onStepBackward when Step Back button is clicked', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} />);

      await user.click(screen.getByText('⏮ Step Back'));

      expect(defaultProps.onStepBackward).toHaveBeenCalledTimes(1);
    });

    it('should call onPlay when Play button is clicked', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} isPlaying={false} />);

      await user.click(screen.getByText('▶️ Play'));

      expect(defaultProps.onPlay).toHaveBeenCalledTimes(1);
    });

    it('should call onPause when Pause button is clicked', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} isPlaying={true} />);

      await user.click(screen.getByText('⏸️ Pause'));

      expect(defaultProps.onPause).toHaveBeenCalledTimes(1);
    });

    it('should call onStepForward when Step Forward button is clicked', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} />);

      await user.click(screen.getByText('⏭ Step Forward'));

      expect(defaultProps.onStepForward).toHaveBeenCalledTimes(1);
    });

    it('should call onShowAll when Fin button is clicked', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} />);

      await user.click(screen.getByText('⏩ Fin'));

      expect(defaultProps.onShowAll).toHaveBeenCalledTimes(1);
    });
  });

  describe('Speed slider', () => {
    it('should call onSpeedChange with correct value when slider changes', () => {
      render(<Toolbar {...defaultProps} />);

      const slider = screen.getByRole('slider', { name: /speed/i });
      fireEvent.change(slider, { target: { value: '75' } });

      expect(defaultProps.onSpeedChange).toHaveBeenCalledWith(75);
    });

    it('should reflect speed prop value', () => {
      render(<Toolbar {...defaultProps} speed={25} />);

      const slider = screen.getByRole('slider', { name: /speed/i });
      expect(slider).toHaveValue('25');
    });

    it('should have correct min and max values', () => {
      render(<Toolbar {...defaultProps} />);

      const slider = screen.getByRole('slider', { name: /speed/i });
      expect(slider).toHaveAttribute('min', '1');
      expect(slider).toHaveAttribute('max', '100');
    });
  });

  describe('Accessibility', () => {
    it('should have title attributes on buttons', () => {
      render(<Toolbar {...defaultProps} />);

      expect(screen.getByText('⏮ Reset')).toHaveAttribute('title', 'Reset to blank canvas');
      expect(screen.getByText('▶️ Play')).toHaveAttribute('title', 'Start playback');
      expect(screen.getByText('⏮ Step Back')).toHaveAttribute('title', 'Go back one stroke');
      expect(screen.getByText('⏭ Step Forward')).toHaveAttribute('title', 'Advance one stroke');
      expect(screen.getByText('⏩ Fin')).toHaveAttribute('title', 'Show all strokes');
    });

    it('should have title attribute on speed slider', () => {
      render(<Toolbar {...defaultProps} speed={42} />);

      const slider = screen.getByRole('slider', { name: /speed/i });
      expect(slider).toHaveAttribute('title', 'Playback speed: 42');
    });
  });

  describe('Highlight strokes toggle', () => {
    it('should render "Highlight strokes" checkbox', () => {
      render(<Toolbar {...defaultProps} />);

      expect(screen.getByRole('checkbox', { name: /highlight strokes/i })).toBeInTheDocument();
    });

    it('should render checkbox unchecked when highlightEnabled is false', () => {
      render(<Toolbar {...defaultProps} highlightEnabled={false} />);

      expect(screen.getByRole('checkbox', { name: /highlight strokes/i })).not.toBeChecked();
    });

    it('should render checkbox checked when highlightEnabled is true', () => {
      render(<Toolbar {...defaultProps} highlightEnabled={true} />);

      expect(screen.getByRole('checkbox', { name: /highlight strokes/i })).toBeChecked();
    });

    it('should call onToggleHighlight(true) when unchecked checkbox is clicked', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} highlightEnabled={false} />);

      await user.click(screen.getByRole('checkbox', { name: /highlight strokes/i }));

      expect(defaultProps.onToggleHighlight).toHaveBeenCalledTimes(1);
      expect(defaultProps.onToggleHighlight).toHaveBeenCalledWith(true);
    });

    it('should call onToggleHighlight(false) when checked checkbox is clicked', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} highlightEnabled={true} />);

      await user.click(screen.getByRole('checkbox', { name: /highlight strokes/i }));

      expect(defaultProps.onToggleHighlight).toHaveBeenCalledTimes(1);
      expect(defaultProps.onToggleHighlight).toHaveBeenCalledWith(false);
    });
  });
});
