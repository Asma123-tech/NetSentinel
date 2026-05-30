import type { Metadata } from 'next';
import './globals.css';
import Providers from '@/components/Providers';

export const metadata: Metadata = {
  title: 'NetSentinel — Safe Search Platform',
  description: 'A secure search environment for safe browsing.',
};

/**
 * Root layout — wraps the whole app with Providers only.
 * AppShell (Header + Sidebar) is rendered by the (main) route group layout,
 * so auth pages (login, signup) get a clean full-screen layout automatically.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}