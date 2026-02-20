/**
 * Unit tests for getArtworkSummaries() in artworks.ts
 *
 * Mocks 'fs' to avoid filesystem access at test time.
 */

import path from 'path';

// Mock fs before importing artworks
jest.mock('fs');

import { readdirSync, readFileSync, existsSync } from 'fs';
import { getArtworkSummaries } from '../artworks';

const mockReaddirSync = readdirSync as jest.MockedFunction<typeof readdirSync>;
const mockReadFileSync = readFileSync as jest.MockedFunction<typeof readFileSync>;
const mockExistsSync = existsSync as jest.MockedFunction<typeof existsSync>;

/** Build a minimal ViewerData JSON string for the given artwork. */
function makeViewerData(opts: {
  artworkId: string;
  artistName?: string;
  subject?: string;
  generationDate?: string | null;
  strokeGenerator?: string | null;
}): string {
  const metadata: Record<string, unknown> = {
    artwork_id: opts.artworkId,
    artist_name: opts.artistName ?? 'Test Artist',
    subject: opts.subject ?? 'Test Subject',
    canvas_width: 800,
    canvas_height: 600,
    background_color: '#FFFFFF',
    total_strokes: 10,
    total_iterations: 5,
    score_progression: [50, 60],
  };

  if (opts.generationDate !== undefined && opts.generationDate !== null) {
    metadata['generation_date'] = opts.generationDate;
  }

  if (opts.strokeGenerator !== undefined && opts.strokeGenerator !== null) {
    metadata['vlm_models'] = {
      stroke_generator: opts.strokeGenerator,
      evaluator: 'test-evaluator',
    };
  }

  return JSON.stringify({ metadata, strokes: [] });
}

/** Create a fake fs.Dirent-like object. */
function makeDirent(name: string): import('fs').Dirent {
  return {
    name,
    isDirectory: () => true,
    isFile: () => false,
    isBlockDevice: () => false,
    isCharacterDevice: () => false,
    isFIFO: () => false,
    isSocket: () => false,
    isSymbolicLink: () => false,
    path: '',
    parentPath: '',
  } as unknown as import('fs').Dirent;
}

const DATA_DIR = path.join(process.cwd(), 'public', 'data');

describe('getArtworkSummaries', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Default sort: newest first by generationDate', () => {
    it('returns artworks sorted descending by generationDate', () => {
      mockExistsSync.mockImplementation((p: unknown) => {
        const filePath = p as string;
        // The public/data dir exists; viewer_data.json files exist; no thumbnails
        if (filePath === DATA_DIR) return true;
        if (filePath.endsWith('viewer_data.json')) return true;
        return false; // thumbnails absent
      });

      mockReaddirSync.mockReturnValue([
        makeDirent('artwork-old'),
        makeDirent('artwork-mid'),
        makeDirent('artwork-new'),
      ] as unknown as ReturnType<typeof readdirSync>);

      mockReadFileSync.mockImplementation((filePath: unknown) => {
        const p = filePath as string;
        if (p.includes('artwork-old'))
          return makeViewerData({
            artworkId: 'artwork-old',
            generationDate: '2024-01-01T00:00:00',
          });
        if (p.includes('artwork-mid'))
          return makeViewerData({
            artworkId: 'artwork-mid',
            generationDate: '2024-06-15T00:00:00',
          });
        if (p.includes('artwork-new'))
          return makeViewerData({
            artworkId: 'artwork-new',
            generationDate: '2025-03-20T00:00:00',
          });
        throw new Error(`Unexpected path: ${p}`);
      });

      const summaries = getArtworkSummaries();

      expect(summaries).toHaveLength(3);
      expect(summaries[0].artworkId).toBe('artwork-new');
      expect(summaries[1].artworkId).toBe('artwork-mid');
      expect(summaries[2].artworkId).toBe('artwork-old');
    });
  });

  describe('Null dates sort to end', () => {
    it('places artworks with null generationDate after those with valid dates', () => {
      mockExistsSync.mockImplementation((p: unknown) => {
        const filePath = p as string;
        if (filePath === DATA_DIR) return true;
        if (filePath.endsWith('viewer_data.json')) return true;
        return false;
      });

      mockReaddirSync.mockReturnValue([
        makeDirent('artwork-nodateb'),
        makeDirent('artwork-dated'),
        makeDirent('artwork-nodatea'),
      ] as unknown as ReturnType<typeof readdirSync>);

      mockReadFileSync.mockImplementation((filePath: unknown) => {
        const p = filePath as string;
        if (p.includes('artwork-nodateb'))
          return makeViewerData({ artworkId: 'artwork-nodateb', generationDate: null });
        if (p.includes('artwork-dated'))
          return makeViewerData({
            artworkId: 'artwork-dated',
            generationDate: '2024-12-01T00:00:00',
          });
        if (p.includes('artwork-nodatea'))
          return makeViewerData({ artworkId: 'artwork-nodatea', generationDate: null });
        throw new Error(`Unexpected path: ${p}`);
      });

      const summaries = getArtworkSummaries();

      expect(summaries).toHaveLength(3);
      // Dated artwork should come first
      expect(summaries[0].artworkId).toBe('artwork-dated');
      // Both null-dated artworks come after
      expect(summaries[1].generationDate).toBeNull();
      expect(summaries[2].generationDate).toBeNull();
    });
  });

  describe('modelName extraction', () => {
    it('sets modelName from vlm_models.stroke_generator when present', () => {
      mockExistsSync.mockImplementation((p: unknown) => {
        const filePath = p as string;
        if (filePath === DATA_DIR) return true;
        if (filePath.endsWith('viewer_data.json')) return true;
        return false;
      });

      mockReaddirSync.mockReturnValue([makeDirent('artwork-with-model')] as unknown as ReturnType<
        typeof readdirSync
      >);

      mockReadFileSync.mockReturnValue(
        makeViewerData({
          artworkId: 'artwork-with-model',
          generationDate: '2025-01-01T00:00:00',
          strokeGenerator: 'claude-sonnet-4-5',
        })
      );

      const summaries = getArtworkSummaries();

      expect(summaries).toHaveLength(1);
      expect(summaries[0].modelName).toBe('claude-sonnet-4-5');
    });

    it('sets modelName to null when vlm_models is absent', () => {
      mockExistsSync.mockImplementation((p: unknown) => {
        const filePath = p as string;
        if (filePath === DATA_DIR) return true;
        if (filePath.endsWith('viewer_data.json')) return true;
        return false;
      });

      mockReaddirSync.mockReturnValue([makeDirent('artwork-no-model')] as unknown as ReturnType<
        typeof readdirSync
      >);

      mockReadFileSync.mockReturnValue(
        makeViewerData({
          artworkId: 'artwork-no-model',
          generationDate: '2025-01-01T00:00:00',
          strokeGenerator: null,
        })
      );

      const summaries = getArtworkSummaries();

      expect(summaries).toHaveLength(1);
      expect(summaries[0].modelName).toBeNull();
    });
  });

  describe('Backward compatibility', () => {
    it('does not throw and defaults generationDate/modelName to null when fields are absent', () => {
      mockExistsSync.mockImplementation((p: unknown) => {
        const filePath = p as string;
        if (filePath === DATA_DIR) return true;
        if (filePath.endsWith('viewer_data.json')) return true;
        return false;
      });

      mockReaddirSync.mockReturnValue([makeDirent('artwork-legacy')] as unknown as ReturnType<
        typeof readdirSync
      >);

      // Viewer data without generation_date or vlm_models
      const legacyData = JSON.stringify({
        metadata: {
          artwork_id: 'artwork-legacy',
          artist_name: 'Old Artist',
          subject: 'Old Subject',
          canvas_width: 640,
          canvas_height: 480,
          background_color: '#000000',
          total_strokes: 5,
          total_iterations: 2,
          score_progression: [40],
        },
        strokes: [],
      });

      mockReadFileSync.mockReturnValue(legacyData);

      expect(() => getArtworkSummaries()).not.toThrow();

      const summaries = getArtworkSummaries();
      expect(summaries).toHaveLength(1);
      expect(summaries[0].generationDate).toBeNull();
      expect(summaries[0].modelName).toBeNull();
    });
  });

  describe('Edge cases', () => {
    it('returns empty array when public/data directory does not exist', () => {
      mockExistsSync.mockReturnValue(false);

      const summaries = getArtworkSummaries();
      expect(summaries).toEqual([]);
    });

    it('skips directories without viewer_data.json', () => {
      mockExistsSync.mockImplementation((p: unknown) => {
        const filePath = p as string;
        if (filePath === DATA_DIR) return true;
        // Only artwork-b has viewer_data.json
        if (filePath.includes('artwork-b') && filePath.endsWith('viewer_data.json')) return true;
        return false;
      });

      mockReaddirSync.mockReturnValue([
        makeDirent('artwork-a'),
        makeDirent('artwork-b'),
      ] as unknown as ReturnType<typeof readdirSync>);

      mockReadFileSync.mockReturnValue(
        makeViewerData({ artworkId: 'artwork-b', generationDate: '2025-01-01T00:00:00' })
      );

      const summaries = getArtworkSummaries();
      expect(summaries).toHaveLength(1);
      expect(summaries[0].artworkId).toBe('artwork-b');
    });
  });
});
