// src/context/SearchSettingsContext.tsx
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import type { FilterMode } from '@/lib/api';
import { fetchSettings, updateSettings } from '@/lib/api';

type Ctx = {
  filterMode: FilterMode;
  setFilterMode: (m: FilterMode) => void;
  loading: boolean;
};

const SearchSettingsContext = createContext<Ctx | null>(null);

export function SearchSettingsProvider({ children }: { children: React.ReactNode }) {
  // OLD:
  // const [filterMode, setFilterModeState] = useState<FilterMode>('strict');
  // NEW:
  const [filterMode, setFilterModeState] = useState<FilterMode>('strict');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const s = await fetchSettings();
        if (mounted && s.filter_mode) {
          setFilterModeState(s.filter_mode);
        }
      } catch (err) {
        console.error('Failed to load settings', err);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const setFilterMode = (m: FilterMode) => {
    setFilterModeState(m);
    updateSettings({ filter_mode: m }).catch((err) => {
      console.error('Failed to update filter mode', err);
    });
  };

  return (
    <SearchSettingsContext.Provider value={{ filterMode, setFilterMode, loading }}>
      {children}
    </SearchSettingsContext.Provider>
  );
}

export function useSearchSettings() {
  const ctx = useContext(SearchSettingsContext);
  if (!ctx) throw new Error('useSearchSettings must be used within SearchSettingsProvider');
  return ctx;
}
