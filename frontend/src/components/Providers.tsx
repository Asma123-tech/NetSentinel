// src/components/Providers.tsx
'use client';

import { SearchSettingsProvider } from '@/context/SearchSettingsContext';

export default function Providers({ children }: { children: React.ReactNode }) {
  return <SearchSettingsProvider>{children}</SearchSettingsProvider>;
}
