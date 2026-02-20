/**
 * Build-time artwork data loader.
 *
 * Scans the public/data/ directory for viewer_data.json files and extracts
 * artwork summaries for the homepage gallery.
 */

import { readdirSync, readFileSync, existsSync } from 'fs';
import path from 'path';
import type { ArtworkSummary, ViewerData } from './types';
import { getPublicUrl } from './basePath';

/**
 * Scan the public/data/ directory and build a summary for each artwork.
 *
 * Reads metadata from each artwork's viewer_data.json and checks for
 * the presence of a thumbnail image. Used at build time to generate
 * the static homepage gallery.
 *
 * @returns {ArtworkSummary[]} Array of artwork summaries sorted by artwork ID
 */
export function getArtworkSummaries(): ArtworkSummary[] {
  const dataDir = path.join(process.cwd(), 'public', 'data');

  // Return empty array if directory doesn't exist
  if (!existsSync(dataDir)) {
    console.warn('public/data directory not found');
    return [];
  }

  try {
    const entries = readdirSync(dataDir, { withFileTypes: true });
    const summaries: ArtworkSummary[] = [];

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;

      const artworkId = entry.name;
      const viewerDataPath = path.join(dataDir, artworkId, 'viewer_data.json');

      // Skip if no viewer_data.json
      if (!existsSync(viewerDataPath)) {
        console.warn(`Skipping ${artworkId}: no viewer_data.json found`);
        continue;
      }

      try {
        // Read and parse viewer data
        const viewerDataContent = readFileSync(viewerDataPath, 'utf-8');
        const viewerData: ViewerData = JSON.parse(viewerDataContent);

        // Check for thumbnail
        const thumbnailPath = path.join(dataDir, artworkId, 'thumbnail.png');
        const thumbnailUrl = existsSync(thumbnailPath)
          ? getPublicUrl(`/data/${artworkId}/thumbnail.png`)
          : null;

        // Build summary
        summaries.push({
          artworkId: viewerData.metadata.artwork_id,
          artistName: viewerData.metadata.artist_name,
          subject: viewerData.metadata.subject,
          totalStrokes: viewerData.metadata.total_strokes,
          totalIterations: viewerData.metadata.total_iterations,
          thumbnailUrl,
          finalScore: viewerData.metadata.final_score ?? null,
        });
      } catch (error) {
        console.warn(`Error reading ${artworkId}:`, error);
        continue;
      }
    }

    // Sort alphabetically by artwork ID
    return summaries.sort((a, b) => a.artworkId.localeCompare(b.artworkId));
  } catch (error) {
    console.error('Error scanning public/data directory:', error);
    return [];
  }
}
