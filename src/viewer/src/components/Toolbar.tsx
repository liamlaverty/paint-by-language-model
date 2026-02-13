'use client';

import Link from 'next/link';

/**
 * Props for the playback toolbar component.
 *
 * @property {() => void} onReset - Reset canvas to blank state
 * @property {() => void} onPlay - Start playback animation
 * @property {() => void} onPause - Pause playback animation
 * @property {() => void} onStepBackward - Go back one stroke
 * @property {() => void} onStepForward - Advance one stroke forward
 * @property {() => void} onShowAll - Skip to the end, showing all strokes
 * @property {boolean} isPlaying - Whether the animation is currently playing
 * @property {boolean} isLoaded - Whether artwork data has been loaded
 * @property {number} speed - Current playback speed (1-100)
 * @property {(speed: number) => void} onSpeedChange - Callback when the speed slider value changes
 * @property {string} infoText - Artwork info text for the toolbar (e.g. "cubist-mary-001 · 42/70 strokes")
 */
interface ToolbarProps {
  onReset: () => void;
  onPlay: () => void;
  onPause: () => void;
  onStepBackward: () => void;
  onStepForward: () => void;
  onShowAll: () => void;
  isPlaying: boolean;
  isLoaded: boolean;
  speed: number;
  onSpeedChange: (speed: number) => void;
  infoText: string;
}

/**
 * Playback toolbar component.
 *
 * Renders transport controls (play/pause/reset/step/show-all) and a speed slider
 * for controlling the stroke-by-stroke animation playback. Also displays artwork
 * info text and a link back to the gallery.
 *
 * @param {ToolbarProps} props - Component props
 * @returns {React.ReactElement} The rendered toolbar
 */
export default function Toolbar({
  onReset,
  onPlay,
  onPause,
  onStepBackward,
  onStepForward,
  onShowAll,
  isPlaying,
  isLoaded,
  speed,
  onSpeedChange,
  infoText,
}: ToolbarProps): React.ReactElement {
  return (
    <div className="toolbar">
      <Link href="/">
        <button type="button" className="button">
          Gallery
        </button>
      </Link>

      <div className="sep" />

      <button
        type="button"
        className="button"
        onClick={onReset}
        disabled={!isLoaded || isPlaying}
        title="Reset to blank canvas"
      >
        ⏮ Reset
      </button>

      <button
        type="button"
        className="button"
        onClick={onStepBackward}
        disabled={!isLoaded || isPlaying}
        title="Go back one stroke"
      >
        ⏮ Step Back
      </button>

      {isPlaying ? (
        <button
          type="button"
          className="button"
          onClick={onPause}
          disabled={!isLoaded}
          title="Pause playback"
        >
          ⏸️ Pause
        </button>
      ) : (
        <button
          type="button"
          className="button"
          onClick={onPlay}
          disabled={!isLoaded}
          title="Start playback"
        >
          ▶️ Play
        </button>
      )}

      <button
        type="button"
        className="button"
        onClick={onStepForward}
        disabled={!isLoaded || isPlaying}
        title="Advance one stroke"
      >
        ⏭ Step Forward
      </button>

      <button
        type="button"
        className="button"
        onClick={onShowAll}
        disabled={!isLoaded || isPlaying}
        title="Show all strokes"
      >
        ⏩ Fin
      </button>

      <div className="sep" />

      <label htmlFor="speed-slider">Speed:</label>
      <input
        id="speed-slider"
        type="range"
        min="1"
        max="100"
        value={speed}
        onChange={(e) => onSpeedChange(Number(e.target.value))}
        disabled={!isLoaded}
        title={`Playback speed: ${speed}`}
      />

      <div className="info">{infoText}</div>
    </div>
  );
}
