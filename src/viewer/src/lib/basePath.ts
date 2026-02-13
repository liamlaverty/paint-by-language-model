/**
 * Utility for constructing URLs that respect the Next.js basePath.
 *
 * When deployed to GitHub Pages at https://liamlaverty.github.io/paint-by-language-model/,
 * all asset URLs need to be prefixed with the basePath.
 */

import { GITHUB_PAGES_BASE_PATH } from '@/config/constants';

/**
 * Get the basePath from Next.js configuration.
 * In production, this will be '/paint-by-language-model', in development it's ''.
 *
 * @returns {string} The basePath for the current environment
 */
export function getBasePath(): string {
  return process.env.NODE_ENV === 'production' ? GITHUB_PAGES_BASE_PATH : '';
}

/**
 * Construct a URL with the correct basePath prefix.
 *
 * @param {string} path - Path relative to the public directory (should start with /)
 * @returns {string} Full path with basePath prefix
 *
 * @example
 * getPublicUrl('/data/artwork-001/thumbnail.png')
 * // Development: '/data/artwork-001/thumbnail.png'
 * // Production: '/paint-by-language-model/data/artwork-001/thumbnail.png'
 */
export function getPublicUrl(path: string): string {
  if (!path.startsWith('/')) {
    console.warn(`Path should start with /: ${path}`);
  }
  return getBasePath() + path;
}
