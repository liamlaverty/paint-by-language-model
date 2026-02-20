/**
 * Artwork preview card component.
 *
 * Displays a single artwork's thumbnail, metadata, and links to the
 * inspector page for detailed viewing.
 */

import Link from 'next/link';
import type { ArtworkSummary } from '@/lib/types';

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
        </div>
      </div>
    </Link>
  );
}
