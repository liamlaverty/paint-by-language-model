'use client';

/**
 * Gallery grid component for displaying artwork previews.
 *
 * Renders a responsive grid of artwork cards or an empty state when
 * no artworks are available. Supports client-side sorting by date,
 * artist name, and model name, as well as filtering by model.
 */

import { useState, useMemo } from 'react';
import ArtworkCard from './ArtworkCard';
import type { ArtworkSummary } from '@/lib/types';

/**
 * Sort option values for the gallery sort control.
 */
type SortOption =
  | 'date-desc'
  | 'date-asc'
  | 'artist-asc'
  | 'artist-desc'
  | 'model-asc'
  | 'model-desc';

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
 * Displays a responsive grid of artwork preview cards with sort and filter
 * controls. Shows an empty state with instructions when no artworks are
 * available. Grid adapts from 1 column (mobile) to 2 (tablet) to 3 (desktop).
 *
 * @param {GalleryProps} props - Component props
 * @returns {React.ReactElement} The rendered gallery grid or empty state
 */
export default function Gallery({ artworks }: GalleryProps): React.ReactElement {
  const [sortBy, setSortBy] = useState<SortOption>('date-desc');
  const [filterModel, setFilterModel] = useState<string>('all');

  // Compute unique model names from artworks
  const models = useMemo(
    () => [...new Set(artworks.map((a) => a.modelName).filter(Boolean))] as string[],
    [artworks]
  );

  // Apply filter then sort
  const displayedArtworks = useMemo(() => {
    let filtered = artworks;
    if (filterModel !== 'all') {
      filtered = artworks.filter((a) => a.modelName === filterModel);
    }
    return [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'date-desc':
          if (!a.generationDate && !b.generationDate) return 0;
          if (!a.generationDate) return 1;
          if (!b.generationDate) return -1;
          return b.generationDate.localeCompare(a.generationDate);
        case 'date-asc':
          if (!a.generationDate && !b.generationDate) return 0;
          if (!a.generationDate) return 1;
          if (!b.generationDate) return -1;
          return a.generationDate.localeCompare(b.generationDate);
        case 'artist-asc':
          return a.artistName.localeCompare(b.artistName);
        case 'artist-desc':
          return b.artistName.localeCompare(a.artistName);
        case 'model-asc':
          return (a.modelName ?? '').localeCompare(b.modelName ?? '');
        case 'model-desc':
          return (b.modelName ?? '').localeCompare(a.modelName ?? '');
      }
    });
  }, [artworks, sortBy, filterModel]);

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

  // Gallery grid with controls
  return (
    <>
      <div className="gallery-controls">
        <div className="gallery-control-group">
          <label htmlFor="sort-select">Sort by:</label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
          >
            <option value="date-desc">Newest first</option>
            <option value="date-asc">Oldest first</option>
            <option value="artist-asc">Artist A → Z</option>
            <option value="artist-desc">Artist Z → A</option>
            <option value="model-asc">Model A → Z</option>
            <option value="model-desc">Model Z → A</option>
          </select>
        </div>
        <div className="gallery-control-group">
          <label htmlFor="model-filter">Model:</label>
          <select
            id="model-filter"
            value={filterModel}
            onChange={(e) => setFilterModel(e.target.value)}
          >
            <option value="all">All models</option>
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <span className="gallery-count">
          Showing {displayedArtworks.length} of {artworks.length} artworks
        </span>
      </div>
      <div className="gallery-grid">
        {displayedArtworks.map((artwork) => (
          <ArtworkCard key={artwork.artworkId} artwork={artwork} />
        ))}
      </div>
    </>
  );
}
