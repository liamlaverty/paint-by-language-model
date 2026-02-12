'use client';

/**
 * Client component for the inspector page.
 *
 * Manages state for stroke visibility, hover/lock selection, animation playback,
 * and speed control. Provides full interactive viewer functionality with keyboard
 * shortcuts.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import StrokeCanvas from '@/components/StrokeCanvas';
import Toolbar from '@/components/Toolbar';
import Timeline from '@/components/Timeline';
import SidePanel from '@/components/SidePanel';
import EmptyState from '@/components/EmptyState';
import type { ViewerData, EnrichedStroke } from '@/lib/types';

/**
 * Props for the inspector client component.
 *
 * @property {string} artworkId - Artwork ID from the URL parameter
 */
interface InspectorClientProps {
  artworkId: string;
}

/**
 * Inspector client component.
 *
 * Loads artwork data and provides stroke-by-stroke playback controls, timeline
 * scrubbing, hover/click inspection, and keyboard shortcuts for navigation.
 *
 * @param {InspectorClientProps} props - Component props
 * @returns {React.ReactElement} The rendered inspector interface
 */
export default function InspectorClient({ artworkId }: InspectorClientProps): React.ReactElement {
  // State management
  const [viewerData, setViewerData] = useState<ViewerData | null>(null);
  const [visibleCount, setVisibleCount] = useState<number>(0);
  const [hoveredIndex, setHoveredIndex] = useState<number>(-1);
  const [lockedIndex, setLockedIndex] = useState<number>(-1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(50);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  // Animation timer ref
  const animTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /**
   * Calculate animation delay from speed slider value.
   *
   * Maps speed slider (1-100) to delay (500ms → 10ms).
   *
   * @param {number} speedValue - Speed slider value (1-100)
   * @returns {number} Delay in milliseconds
   */
  const getDelay = (speedValue: number): number => {
    return Math.max(10, 500 - (speedValue - 1) * 5);
  };

  /**
   * Animation step function.
   *
   * Advances one stroke and schedules the next step if not complete.
   * Auto-shows metadata for the latest stroke if not locked.
   */
  const animationStep = useCallback(() => {
    if (!viewerData) return;

    setVisibleCount((prev) => {
      const next = prev + 1;
      const total = viewerData.strokes.length;

      if (next >= total) {
        // Animation complete
        setIsPlaying(false);
        return total;
      }

      // Schedule next step
      animTimerRef.current = setTimeout(animationStep, getDelay(speed));

      // Auto-show metadata for latest stroke if not locked
      if (lockedIndex === -1) {
        setHoveredIndex(next - 1);
      }

      return next;
    });
  }, [viewerData, speed, lockedIndex]);

  /**
   * Start playback animation.
   */
  const play = useCallback(() => {
    if (!viewerData) return;
    if (visibleCount >= viewerData.strokes.length) return;

    setIsPlaying(true);
    animTimerRef.current = setTimeout(animationStep, getDelay(speed));
  }, [viewerData, visibleCount, speed, animationStep]);

  /**
   * Pause playback animation.
   */
  const pause = useCallback(() => {
    setIsPlaying(false);
    if (animTimerRef.current) {
      clearTimeout(animTimerRef.current);
      animTimerRef.current = null;
    }
  }, []);

  /**
   * Step forward one stroke.
   */
  const stepForward = useCallback(() => {
    if (!viewerData) return;
    if (isPlaying) pause();

    setVisibleCount((prev) => {
      const next = Math.min(prev + 1, viewerData.strokes.length);

      // Auto-show metadata if not locked
      if (lockedIndex === -1 && next > 0) {
        setHoveredIndex(next - 1);
      }

      return next;
    });
  }, [viewerData, isPlaying, lockedIndex, pause]);

  /**
   * Step backward one stroke.
   */
  const stepBackward = useCallback(() => {
    if (!viewerData) return;
    if (isPlaying) pause();

    setVisibleCount((prev) => Math.max(prev - 1, 0));
  }, [viewerData, isPlaying, pause]);

  /**
   * Reset to blank canvas.
   */
  const reset = useCallback(() => {
    pause();
    setVisibleCount(0);
    setLockedIndex(-1);
    setHoveredIndex(-1);
  }, [pause]);

  /**
   * Show all strokes.
   */
  const showAll = useCallback(() => {
    if (!viewerData) return;
    pause();
    setVisibleCount(viewerData.strokes.length);
  }, [viewerData, pause]);

  /**
   * Handle stroke hover.
   *
   * @param {number} index - Stroke index (-1 for none)
   */
  const handleStrokeHover = useCallback(
    (index: number) => {
      if (lockedIndex === -1) {
        setHoveredIndex(index);
      }
    },
    [lockedIndex]
  );

  /**
   * Handle stroke click (lock selection).
   *
   * @param {number} index - Stroke index
   */
  const handleStrokeClick = useCallback((index: number) => {
    setLockedIndex(index);
    setHoveredIndex(-1);
  }, []);

  /**
   * Handle background click (clear selection).
   */
  const handleBackgroundClick = useCallback(() => {
    setLockedIndex(-1);
    setHoveredIndex(-1);
  }, []);

  /**
   * Clear locked selection.
   */
  const clearSelection = useCallback(() => {
    setLockedIndex(-1);
    setHoveredIndex(-1);
  }, []);

  /**
   * Handle timeline scrubber change.
   *
   * @param {number} value - New visible count
   */
  const handleTimelineChange = useCallback(
    (value: number) => {
      if (isPlaying) pause();
      setVisibleCount(value);
    },
    [isPlaying, pause]
  );

  /**
   * Handle speed slider change.
   *
   * @param {number} newSpeed - New speed value (1-100)
   */
  const handleSpeedChange = useCallback((newSpeed: number) => {
    setSpeed(newSpeed);
  }, []);

  // Load viewer data on mount
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError('');

      try {
        const response = await fetch(`/data/${artworkId}/viewer_data.json`);
        if (!response.ok) {
          throw new Error(`Failed to load artwork: ${response.statusText}`);
        }

        const data: ViewerData = await response.json();
        setViewerData(data);
        // Show all strokes initially (matching vanilla viewer behavior)
        setVisibleCount(data.strokes.length);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('Error loading viewer data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [artworkId]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (animTimerRef.current) {
        clearTimeout(animTimerRef.current);
      }
    };
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if typing in an input element
      if (e.target && (e.target as HTMLElement).tagName === 'INPUT') {
        return;
      }

      switch (e.key) {
        case ' ':
          e.preventDefault();
          if (isPlaying) {
            pause();
          } else {
            play();
          }
          break;
        case 'ArrowRight':
          e.preventDefault();
          stepForward();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          stepBackward();
          break;
        case 'Home':
          e.preventDefault();
          reset();
          break;
        case 'End':
          e.preventDefault();
          showAll();
          break;
        case 'Escape':
          e.preventDefault();
          clearSelection();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isPlaying, play, pause, stepForward, stepBackward, reset, showAll, clearSelection]);

  // Computed values
  const displayedStroke: EnrichedStroke | null =
    lockedIndex >= 0 && viewerData
      ? viewerData.strokes[lockedIndex]
      : hoveredIndex >= 0 && viewerData
        ? viewerData.strokes[hoveredIndex]
        : null;

  const highlightedIndex = lockedIndex >= 0 ? lockedIndex : hoveredIndex;

  const infoText = viewerData
    ? `${viewerData.metadata.artwork_id} · ${visibleCount}/${viewerData.metadata.total_strokes} strokes`
    : '';

  return (
    <div className="viewer-container">
      <Toolbar
        onReset={reset}
        onPlay={play}
        onPause={pause}
        onStepForward={stepForward}
        onShowAll={showAll}
        isPlaying={isPlaying}
        isLoaded={viewerData !== null}
        speed={speed}
        onSpeedChange={handleSpeedChange}
        infoText={infoText}
      />

      <div className="content-grid">
        <div className="canvas-container">
          {viewerData ? (
            <StrokeCanvas
              strokes={viewerData.strokes}
              metadata={viewerData.metadata}
              visibleCount={visibleCount}
              onStrokeHover={handleStrokeHover}
              onStrokeClick={handleStrokeClick}
              onBackgroundClick={handleBackgroundClick}
              lockedIndex={lockedIndex}
              highlightedIndex={highlightedIndex}
            />
          ) : (
            <EmptyState isLoading={isLoading} error={error} />
          )}
        </div>

        {viewerData && (
          <SidePanel
            stroke={displayedStroke}
            metadata={viewerData.metadata}
            isLocked={lockedIndex >= 0}
            onClearSelection={clearSelection}
          />
        )}
      </div>

      {viewerData && (
        <Timeline
          current={visibleCount}
          total={viewerData.strokes.length}
          onChange={handleTimelineChange}
        />
      )}
    </div>
  );
}
