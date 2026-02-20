/**
 * Shared formatting utility functions for the viewer UI.
 */

/**
 * Format an ISO 8601 date string to UK format (DD/MM/YYYY).
 *
 * @param {string | null | undefined} isoDate - ISO 8601 date string
 * @returns {string} Formatted date or empty string if input is null/invalid
 */
export function formatDateUK(isoDate: string | null | undefined): string {
  if (!isoDate) return '';
  try {
    const date = new Date(isoDate);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return '';
  }
}

/**
 * Get a CSS color for a score value.
 *
 * Returns red for scores below 40, amber for 40-69, green for 70+.
 *
 * @param {number} score - Score value (0-100)
 * @returns {string} CSS hex color string
 */
export function getScoreColor(score: number): string {
  if (score < 40) return '#ef4444';
  if (score < 70) return '#f59e0b';
  return '#22c55e';
}
