'use client';

/**
 * Props for the empty/loading state placeholder.
 *
 * @property {boolean} isLoading - Whether data is currently loading
 * @property {string} [error] - Optional error message to display
 */
interface EmptyStateProps {
  isLoading: boolean;
  error?: string;
}

/**
 * Empty state placeholder component.
 *
 * Displays loading, error, or default "no artwork loaded" states in the canvas
 * area when no artwork data is available. Used to provide visual feedback while
 * data is being fetched or when an error occurs.
 *
 * @param {EmptyStateProps} props - Component props
 * @returns {React.ReactElement} The rendered empty state
 */
export default function EmptyState({ isLoading, error }: EmptyStateProps): React.ReactElement {
  // Error state
  if (error && error.length > 0) {
    return (
      <div className="empty-state">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
          />
        </svg>
        <p>Error loading artwork</p>
        <small>{error}</small>
        <small>Please try refreshing the page</small>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="empty-state">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          style={{ animation: 'spin 1s linear infinite' }}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
          />
        </svg>
        <p>Loading artwork...</p>
        <style>{`
          @keyframes spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }
        `}</style>
      </div>
    );
  }

  // Default state (no artwork loaded)
  return (
    <div className="empty-state">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9.53 16.122a3 3 0 00-5.78 1.128 2.25 2.25 0 01-2.4 2.245 4.5 4.5 0 008.4-2.245c0-.399-.078-.78-.22-1.128zm0 0a15.998 15.998 0 003.388-1.62m-5.043-.025a15.994 15.994 0 011.622-3.395m3.42 3.42a15.995 15.995 0 004.764-4.648l3.876-5.814a1.151 1.151 0 00-1.597-1.597L14.146 6.32a15.996 15.996 0 00-4.649 4.763m3.42 3.42a6.776 6.776 0 00-3.42-3.42"
        />
      </svg>
      <p>No artwork loaded</p>
      <small>Select an artwork from the gallery</small>
    </div>
  );
}
