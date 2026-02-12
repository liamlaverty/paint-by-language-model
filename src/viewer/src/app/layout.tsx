import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Paint by Language Model - Viewer',
  description: 'Interactive stroke-by-stroke viewer for VLM-generated artwork',
};

/**
 * Root layout component for the Next.js app.
 *
 * Provides the HTML structure and global styles. Full implementation
 * will be completed in Task 5.
 *
 * @param {object} props - Component props
 * @param {React.ReactNode} props.children - Child components to render
 *
 * @returns {JSX.Element} - The root layout
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
