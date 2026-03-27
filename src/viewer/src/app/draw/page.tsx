import type React from 'react';
import DrawPage from '@/components/DrawPage';

export const metadata = {
  title: 'Draw — Paint by Language Model',
  description: 'Interactive canvas for manual stroke drawing',
};

/**
 * Route component for the /draw page.
 *
 * Thin server-component wrapper that renders the DrawPage client component.
 *
 * @returns {React.ReactElement} The draw page
 */
export default function DrawRoute(): React.ReactElement {
  return <DrawPage />;
}
