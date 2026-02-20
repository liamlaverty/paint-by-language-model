/**
 * Artwork preview card component.
 *
 * Displays a single artwork's thumbnail, metadata, and links to the
 * inspector page for detailed viewing.
 */

import Link from 'next/link';
import type { ArtworkSummary } from '@/lib/types';
import { getScoreColor } from '../lib/format-utils';

/**
 * Props for a single artwork preview card.
 *
 * @property {ArtworkSummary} artwork - Artwork summary data
 */
interface ArtworkCardProps {
  artwork: ArtworkSummary;
}

/**
 * Artwork card component.
 *
 * Renders a preview card with thumbnail (or placeholder), artist name,
 * subject, and stroke/iteration counts. Links to the inspector page for
 * detailed stroke-by-stroke viewing. Features hover effects for interactivity.
 *
 * @param {ArtworkCardProps} props - Component props
 * @returns {React.ReactElement} The rendered artwork card
 */
/**
 * Returns a CSS class name for the score badge based on the score value.
 *
 * @param {number} score - The final score value
 * @returns {string} CSS class name for the badge color
 */
function getScoreClass(score: number): string {
  if (score < 40) return 'badge-score-low';
  if (score < 70) return 'badge-score-mid';
  return 'badge-score-high';
}

export default function ArtworkCard({ artwork }: ArtworkCardProps): React.ReactElement {
  // Truncate subject if too long
  const truncatedSubject =
    artwork.subject.length > 80 ? `${artwork.subject.slice(0, 77)}…` : artwork.subject;

  return (
    <Link href={`/inspect/${artwork.artworkId}`} className="artwork-card">
      <div className="thumbnail">
        {artwork.thumbnailUrl ? (
          <img src={artwork.thumbnailUrl} alt={`${artwork.artistName} - ${artwork.subject}`} />
        ) : (
          <div className="thumbnail-placeholder">
            <span>{artwork.artworkId}</span>
          </div>
        )}
      </div>
      <div className="card-body">
        <h3 className="card-title">{artwork.artistName}</h3>
        <p className="card-subject">{truncatedSubject}</p>
        <div className="badges">
          <span className="badge">{artwork.totalStrokes} strokes</span>
          <span className="badge">{artwork.totalIterations} iterations</span>
          {artwork.modelName && <span className="badge badge-model">{artwork.modelName}</span>}
          {artwork.finalScore != null && (
            <span className={`badge badge-score ${getScoreClass(artwork.finalScore)}`}>
              Score: {artwork.finalScore}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
