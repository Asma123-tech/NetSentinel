import AppShell from '@/components/AppShell';

/**
 * Main route group layout.
 * All pages inside (main)/ get the full AppShell (Header + Sidebar).
 * Route group folders do NOT change the URL:
 *   app/(main)/search/page.tsx    →  /search
 *   app/(main)/dashboard/page.tsx →  /dashboard
 *   etc.
 */
export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}