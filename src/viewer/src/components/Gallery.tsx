/**
 * Gallery grid component for displaying artwork previews.
 *
 * Renders a responsive grid of artwork cards or an empty state when
 * no artworks are available.
 */

import ArtworkCard from './ArtworkCard';
import type { ArtworkSummary } from '@/lib/types';

/**
 * Props for the artwork gallery grid.
 *
 * @property {ArtworkSummary[]} artworks - Array of artwork summaries to display
 */
interface GalleryProps {
  artworks: ArtworkSummary[];
}

/**
 * Gallery grid component.
 *
 * Displays a responsive grid of artwork preview cards. Shows an empty
 * state with instructions when no artworks are available. Grid adapts
 * from 1 column (mobile) to 2 (tablet) to 3 (desktop).
 *
 * @param {GalleryProps} props - Component props
 * @returns {React.ReactElement} The rendered gallery grid or empty state
 */
export default function Gallery({ artworks }: GalleryProps): React.ReactElement {
  // Empty state
  if (artworks.length === 0) {
    return (
      <div className="gallery-empty">
        <h2>No artworks available</h2>
        <p>
          The gallery is currently empty. Check back soon to explore artwork created by vision
          language models.
        </p>
      </div>
    );
  }

  // Gallery grid
  return (
    <div className="gallery-grid">
      {artworks.map((artwork) => (
        <ArtworkCard key={artwork.artworkId} artwork={artwork} />
      ))}
    </div>
  );
}
