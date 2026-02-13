/**
 * Homepage displaying a gallery of all generated artworks.
 *
 * Loads artwork summaries at build time from public/data/ and renders
 * a responsive grid of preview cards linking to the inspector.
 *
 * @returns {React.ReactElement} The gallery page
 */
import Gallery from '@/components/Gallery';
import { getArtworkSummaries } from '@/lib/artworks';

export default function HomePage(): React.ReactElement {
  const artworks = getArtworkSummaries();

  return (
    <main className="gallery-page">
      <div className="gallery-header">
        <h1>Generated Artworks</h1>
        <p>Explore artwork created by vision language models, stroke by stroke</p>
      </div>
      <Gallery artworks={artworks} />
    </main>
  );
}
