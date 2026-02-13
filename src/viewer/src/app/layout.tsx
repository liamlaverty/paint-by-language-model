import type { Metadata } from 'next';
import Script from 'next/script';
import './globals.css';

export const metadata: Metadata = {
  title: 'Paint by Language Model - Viewer',
  description: 'Interactive stroke-by-stroke viewer for VLM-generated artwork',
};

const isProduction = process.env.NODE_ENV === 'production';

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
        {isProduction && (
          <Script
            defer
            src="https://cloud.umami.is/script.js"
            data-website-id="6489b7ae-3b0b-4d6f-9e32-fd5b266a592d"
            strategy="afterInteractive"
          />
        )}
        <main>{children}</main>
      </body>
    </html>
  );
}
