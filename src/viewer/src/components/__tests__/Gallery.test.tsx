/**
 * Unit tests for Gallery component
 *
 * Tests sort/filter controls, model filter, and empty state.
 */

import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Gallery from '@/components/Gallery';
import type { ArtworkSummary } from '@/lib/types';

// Mock next/link so ArtworkCard renders without router context
jest.mock('next/link', () => {
  const MockLink = ({
    href,
    children,
    className,
  }: {
    href: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  );
  MockLink.displayName = 'MockLink';
  return MockLink;
});

/** Helper: build a minimal ArtworkSummary */
function makeArtwork(overrides: Partial<ArtworkSummary> & { artworkId: string }): ArtworkSummary {
  return {
    artworkId: overrides.artworkId,
    artistName: overrides.artistName ?? 'Test Artist',
    subject: overrides.subject ?? 'Test Subject',
    totalStrokes: overrides.totalStrokes ?? 10,
    totalIterations: overrides.totalIterations ?? 5,
    thumbnailUrl: overrides.thumbnailUrl ?? null,
    generationDate: overrides.generationDate ?? null,
    modelName: overrides.modelName ?? null,
  };
}

const OLD_ARTWORK = makeArtwork({
  artworkId: 'artwork-old',
  artistName: 'Monet',
  subject: 'Water Lilies',
  generationDate: '2024-01-01T00:00:00',
  modelName: 'model-a',
});

const MID_ARTWORK = makeArtwork({
  artworkId: 'artwork-mid',
  artistName: 'Kandinsky',
  subject: 'Composition',
  generationDate: '2024-06-15T00:00:00',
  modelName: 'model-b',
});

const NEW_ARTWORK = makeArtwork({
  artworkId: 'artwork-new',
  artistName: 'Lowry',
  subject: 'Mill Workers',
  generationDate: '2025-03-20T00:00:00',
  modelName: 'model-a',
});

/** Get artworkId values of all rendered artwork cards (via href on links). */
function getRenderedCardIds(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll('a.artwork-card')).map((a) => {
    const href = a.getAttribute('href') ?? '';
    return href.replace('/inspect/', '');
  });
}

describe('Gallery', () => {
  describe('Empty state', () => {
    it('renders "No artworks available" when artworks array is empty', () => {
      render(<Gallery artworks={[]} />);

      expect(screen.getByText('No artworks available')).toBeInTheDocument();
    });

    it('does not render sort/filter controls in empty state', () => {
      render(<Gallery artworks={[]} />);

      expect(screen.queryByLabelText(/sort by/i)).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/model/i)).not.toBeInTheDocument();
    });
  });

  describe('Sort dropdown', () => {
    it('renders the sort dropdown with "Newest first" selected by default', () => {
      render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      const sortSelect = screen.getByRole('combobox', { name: /sort by/i });
      expect(sortSelect).toBeInTheDocument();
      expect(sortSelect).toHaveValue('date-desc');
      // The displayed option text
      expect(within(sortSelect).getByRole('option', { name: 'Newest first' })).toBeInTheDocument();
    });

    it('renders cards in newest-first order by default', () => {
      const { container } = render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      const ids = getRenderedCardIds(container);
      expect(ids[0]).toBe('artwork-new');
      expect(ids[1]).toBe('artwork-mid');
      expect(ids[2]).toBe('artwork-old');
    });

    it('re-orders cards when sort is changed to "Oldest first"', async () => {
      const user = userEvent.setup();
      const { container } = render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      const sortSelect = screen.getByRole('combobox', { name: /sort by/i });
      await user.selectOptions(sortSelect, 'date-asc');

      const ids = getRenderedCardIds(container);
      expect(ids[0]).toBe('artwork-old');
    });

    it('re-orders cards when sort is changed to "Artist A → Z"', async () => {
      const user = userEvent.setup();
      const { container } = render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      const sortSelect = screen.getByRole('combobox', { name: /sort by/i });
      await user.selectOptions(sortSelect, 'artist-asc');

      const ids = getRenderedCardIds(container);
      // Alphabetically: Kandinsky, Lowry, Monet
      expect(ids[0]).toBe('artwork-mid'); // Kandinsky
    });
  });

  describe('Model filter dropdown', () => {
    it('renders "All models" option and unique model names', () => {
      render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      const modelSelect = screen.getByRole('combobox', { name: /model/i });
      expect(within(modelSelect).getByRole('option', { name: 'All models' })).toBeInTheDocument();
      expect(within(modelSelect).getByRole('option', { name: 'model-a' })).toBeInTheDocument();
      expect(within(modelSelect).getByRole('option', { name: 'model-b' })).toBeInTheDocument();
      // model-a appears in two artworks but should only be listed once
      expect(within(modelSelect).getAllByRole('option', { name: 'model-a' })).toHaveLength(1);
    });

    it('shows only matching artworks when filtered by model', async () => {
      const user = userEvent.setup();
      const { container } = render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      const modelSelect = screen.getByRole('combobox', { name: /model/i });
      await user.selectOptions(modelSelect, 'model-b');

      const ids = getRenderedCardIds(container);
      expect(ids).toHaveLength(1);
      expect(ids[0]).toBe('artwork-mid');
    });

    it('shows all artworks when "All models" is selected', async () => {
      const user = userEvent.setup();
      const { container } = render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      // First narrow then reset
      const modelSelect = screen.getByRole('combobox', { name: /model/i });
      await user.selectOptions(modelSelect, 'model-a');
      await user.selectOptions(modelSelect, 'all');

      const ids = getRenderedCardIds(container);
      expect(ids).toHaveLength(3);
    });

    it('filtering by model-a shows two artworks', async () => {
      const user = userEvent.setup();
      const { container } = render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      const modelSelect = screen.getByRole('combobox', { name: /model/i });
      await user.selectOptions(modelSelect, 'model-a');

      const ids = getRenderedCardIds(container);
      expect(ids).toHaveLength(2);
      expect(ids).toContain('artwork-old');
      expect(ids).toContain('artwork-new');
    });
  });

  describe('Count display', () => {
    it('shows correct artwork count', () => {
      render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      expect(screen.getByText('Showing 3 of 3 artworks')).toBeInTheDocument();
    });

    it('updates count when filter narrows results', async () => {
      const user = userEvent.setup();
      render(<Gallery artworks={[OLD_ARTWORK, MID_ARTWORK, NEW_ARTWORK]} />);

      const modelSelect = screen.getByRole('combobox', { name: /model/i });
      await user.selectOptions(modelSelect, 'model-b');

      expect(screen.getByText('Showing 1 of 3 artworks')).toBeInTheDocument();
    });
  });

  describe('Artworks without modelName', () => {
    it('does not error on artworks with null modelName', () => {
      const noModelArtwork = makeArtwork({ artworkId: 'artwork-nomodel', modelName: null });
      expect(() => render(<Gallery artworks={[noModelArtwork]} />)).not.toThrow();
    });

    it('does not include null in model filter options', () => {
      const noModelArtwork = makeArtwork({ artworkId: 'artwork-nomodel', modelName: null });
      render(<Gallery artworks={[noModelArtwork]} />);

      const modelSelect = screen.getByRole('combobox', { name: /model/i });
      const options = within(modelSelect).getAllByRole('option');
      // Should only have "All models"
      expect(options).toHaveLength(1);
      expect(options[0]).toHaveTextContent('All models');
    });
  });
});
