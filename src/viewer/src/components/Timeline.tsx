'use client';

/**
 * Props for the timeline scrubber component.
 *
 * @property {number} current - Current stroke position in the animation
 * @property {number} total - Total number of strokes
 * @property {(value: number) => void} onChange - Callback when the scrubber value changes
 */
interface TimelineProps {
  current: number;
  total: number;
  onChange: (value: number) => void;
}

/**
 * Timeline scrubber component.
 *
 * Renders a range input slider for navigating through the stroke sequence,
 * along with a label showing the current position out of the total. Hidden
 * when no data is loaded (total === 0).
 *
 * @param {TimelineProps} props - Component props
 * @returns {React.ReactElement | null} The rendered timeline scrubber, or null if no data is loaded
 */
export default function Timeline({
  current,
  total,
  onChange,
}: TimelineProps): React.ReactElement | null {
  // Hide when no data is loaded
  if (total === 0) {
    return null;
  }

  return (
    <div className="timeline">
      <input
        type="range"
        min="0"
        max={total}
        value={current}
        onChange={(e) => onChange(Number(e.target.value))}
        title={`Stroke ${current} of ${total}`}
      />
      <div className="timeline-label" style={{ minWidth: '90px', fontFamily: 'var(--font-mono)' }}>
        {current} / {total}
      </div>
    </div>
  );
}
