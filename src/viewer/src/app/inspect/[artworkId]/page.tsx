/**
 * Inspector page for viewing and interacting with generated artwork.
 *
 * Server component that generates static params at build time and renders
 * the interactive InspectorClient component with the artwork ID.
 */

import { Suspense } from 'react';
import { promises as fs, existsSync } from 'fs';
import path from 'path';
import InspectorClient from './InspectorClient';

/**
 * Generate static route parameters for all artworks.
 *
 * Reads the public/data/ directory at build time to discover all
 * artwork IDs and pre-render an inspector page for each.
 *
 * @returns {Promise<{ artworkId: string }[]>} Array of route params
 */
export async function generateStaticParams(): Promise<{ artworkId: string }[]> {
  const dataDir = path.join(process.cwd(), 'public', 'data');

  try {
    const entries = await fs.readdir(dataDir, { withFileTypes: true });
    const artworkIds = entries
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .filter((name) => {
        // Only include directories that have viewer_data.json
        const viewerDataPath = path.join(dataDir, name, 'viewer_data.json');
        return existsSync(viewerDataPath);
      });

    return artworkIds.map((id) => ({ artworkId: id }));
  } catch (error) {
    // Directory doesn't exist at build time - return empty array
    console.warn('public/data directory not found at build time:', error);
    return [];
  }
}

/**
 * Inspector page props.
 *
 * @property {Promise<object>} params - Route parameters (async in Next.js 15+)
 * @property {string} params.artworkId - Artwork ID from the URL
 */
interface PageProps {
  params: Promise<{ artworkId: string }>;
}

/**
 * Inspector page component.
 *
 * Server component wrapper that renders the interactive InspectorClient
 * with the artwork ID from the route parameters. The optional `?stroke=N`
 * deep-link param is read client-side inside InspectorClient via
 * useSearchParams(), keeping this page fully statically renderable.
 *
 * @param {PageProps} props - Page props
 * @returns {Promise<React.ReactElement>} The rendered inspector page
 */
export default async function InspectorPage({ params }: PageProps): Promise<React.ReactElement> {
  const { artworkId } = await params;
  return (
    <Suspense>
      <InspectorClient artworkId={artworkId} />
    </Suspense>
  );
}
