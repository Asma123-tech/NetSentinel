/**
 * Auth route group layout.
 * Login and signup pages get a clean full-screen layout — no Header or Sidebar.
 * Next.js route groups (parentheses folders) do NOT affect the URL:
 *   app/(auth)/login/page.tsx  →  /login
 *   app/(auth)/signup/page.tsx →  /signup
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}