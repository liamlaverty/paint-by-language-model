import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Paint by Language Model - Viewer',
  description: 'Interactive stroke-by-stroke viewer for VLM-generated artwork',
};

/**
 * Root layout wrapping all pages with navigation and global styles.
 *
 * @param {object} props - Layout props
 * @param {React.ReactNode} props.children - The page content to render
 *
 * @returns {JSX.Element} - The root HTML structure
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
