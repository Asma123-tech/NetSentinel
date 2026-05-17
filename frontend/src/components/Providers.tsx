'use client';

import { AuthProvider } from '@/context/AuthContext';
import { SearchSettingsProvider } from '@/context/SearchSettingsContext';

// AuthProvider must be outermost so useAuth() works everywhere
// including inside Header, Sidebar, and ProtectedRoute
export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <SearchSettingsProvider>
        {children}
      </SearchSettingsProvider>
    </AuthProvider>
  );
}
