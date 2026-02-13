/**
 * Tests for basePath utility
 */

import { getPublicUrl, getBasePath } from '../basePath';
import { GITHUB_PAGES_BASE_PATH } from '@/config/constants';

describe('basePath utility', () => {
  const originalEnv = process.env.NODE_ENV;

  afterEach(() => {
    (process.env as { NODE_ENV?: string }).NODE_ENV = originalEnv;
  });

  describe('getBasePath', () => {
    it('should return empty string in development', () => {
      (process.env as { NODE_ENV?: string }).NODE_ENV = 'development';
      expect(getBasePath()).toBe('');
    });

    it('should return /paint-by-language-model in production', () => {
      (process.env as { NODE_ENV?: string }).NODE_ENV = 'production';
      expect(getBasePath()).toBe(GITHUB_PAGES_BASE_PATH);
    });
  });

  describe('getPublicUrl', () => {
    it('should return path as-is in development', () => {
      (process.env as { NODE_ENV?: string }).NODE_ENV = 'development';
      const result = getPublicUrl('/data/artwork-001/thumbnail.png');
      expect(result).toBe('/data/artwork-001/thumbnail.png');
    });

    it('should prepend basePath in production', () => {
      (process.env as { NODE_ENV?: string }).NODE_ENV = 'production';
      const result = getPublicUrl('/data/artwork-001/thumbnail.png');
      expect(result).toBe(`${GITHUB_PAGES_BASE_PATH}/data/artwork-001/thumbnail.png`);
    });

    it('should handle viewer_data.json paths', () => {
      (process.env as { NODE_ENV?: string }).NODE_ENV = 'production';
      const result = getPublicUrl('/data/artwork-001/viewer_data.json');
      expect(result).toBe(`${GITHUB_PAGES_BASE_PATH}/data/artwork-001/viewer_data.json`);
    });

    it('should warn if path does not start with /', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      getPublicUrl('data/artwork-001/thumbnail.png');
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Path should start with /'));
      consoleSpy.mockRestore();
    });

    it('should handle root path', () => {
      (process.env as { NODE_ENV?: string }).NODE_ENV = 'production';
      const result = getPublicUrl('/');
      expect(result).toBe(`${GITHUB_PAGES_BASE_PATH}/`);
    });
  });
});
