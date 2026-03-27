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
 * @property {boolean} highlightEnabled - Whether the stroke highlight overlay is enabled during playback
 * @property {(enabled: boolean) => void} onToggleHighlight - Callback to toggle the highlight state
 * @property {() => void} onCopyUrl - Copy a deep-link URL for the current stroke count to the clipboard
 * @property {() => void} onDownloadJSON - Download the currently-visible strokes as a DrawingData v1 JSON file
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
  highlightEnabled: boolean;
  onToggleHighlight: (enabled: boolean) => void;
  onCopyUrl: () => void;
  onDownloadJSON: () => void;
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
  highlightEnabled,
  onToggleHighlight,
  onCopyUrl,
  onDownloadJSON,
}: ToolbarProps): React.ReactElement {
  return (
    <div className="toolbar">
      {/* <Link href="/">
        <button type="button" className="button">
          Home
        </button>
      </Link> */}

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

      <div className="sep" />
      <label className="toolbar-toggle">
        <input
          type="checkbox"
          checked={highlightEnabled}
          onChange={(e) => onToggleHighlight(e.target.checked)}
        />
        Highlight strokes
      </label>

      <div className="sep" />

      <button
        type="button"
        className="button"
        onClick={onCopyUrl}
        disabled={!isLoaded}
        title="Copy a deep-link URL for the current stroke to the clipboard"
      >
        Share
      </button>

      <button
        type="button"
        className="button"
        onClick={onDownloadJSON}
        disabled={!isLoaded}
        title="Download visible strokes as ax JSON file"
      >
        Get JSON
      </button>

      <div className="info">{infoText}</div>
    </div>
  );
}
