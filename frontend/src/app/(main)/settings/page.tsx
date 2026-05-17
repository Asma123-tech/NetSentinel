'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useSearchSettings } from '@/context/SearchSettingsContext';
import {
  fetchSettings,
  updateSettings,
  clearSearchHistory,
  exportSearchHistoryCsv,
  type BackendSettings,
} from '@/lib/api';

export default function SettingsPage() {
  const { filterMode, setFilterMode } = useSearchSettings();

  const [notifications, setNotifications] = useState(true);
  const [parentalControls, setParentalControls] = useState(true);
  const [searchHistory, setSearchHistory] = useState(true);
  const [blockedKeywords, setBlockedKeywords] = useState('');
  const [allowedDomains, setAllowedDomains] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const s = await fetchSettings();
        if (!mounted) return;
        setNotifications(s.notifications);
        setParentalControls(s.parental_controls);
        setSearchHistory(s.save_search_history);
        setBlockedKeywords(s.blocked_keywords || '');
        setAllowedDomains(s.allowed_domains || '');
        setFilterMode(s.filter_mode);
      } catch (err: any) {
        console.error(err);
        if (mounted) setError('Failed to load settings');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [setFilterMode]);

  const persist = async (partial: Partial<BackendSettings>) => {
    try {
      setSaving(true);
      setError(null);
      setNotice(null);
      const s = await updateSettings(partial);

      setNotifications(s.notifications);
      setParentalControls(s.parental_controls);
      setSearchHistory(s.save_search_history);
      setBlockedKeywords(s.blocked_keywords || '');
      setAllowedDomains(s.allowed_domains || '');
      setFilterMode(s.filter_mode);
    } catch (err: any) {
      console.error(err);
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="max-w-3xl mx-auto py-12 text-center text-gray-500">Loading settings...</div>;
  }

  return (
    <ProtectedRoute>
      <div className="relative min-h-screen">
        {/* FULL BACKGROUND IMAGE (same as search page) */}
        <div className="fixed inset-0 -z-[5] bg-cover bg-center pointer-events-none blur-md scale-105"
          style={{ backgroundImage: "url('/images/logo 2.jpeg')" }}>
        </div>

        {/* OPTIONAL OVERLAY FOR BETTER READABILITY (same as search page) */}
        <div className="fixed inset-0 -z-[4] bg-white/50 pointer-events-none md:block hidden"></div>
        <div className="fixed inset-0 -z-[4] bg-white/30 pointer-events-none block md:hidden"></div>

        <div className="relative z-10 max-w-3xl mx-auto px-4 py-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 drop-shadow-sm">Settings</h2>

          {error && <div className="mb-4 text-sm text-red-600 font-medium bg-red-50/80 backdrop-blur-sm p-3 rounded-xl border border-red-200">{error}</div>}
          {notice && <div className="mb-4 text-sm text-emerald-700 font-medium bg-emerald-50/80 backdrop-blur-sm p-3 rounded-xl border border-emerald-200">{notice}</div>}

          <Card title="Content Filtering">
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter Mode</label>
            <select
              value={filterMode}
              onChange={(e) => persist({ filter_mode: e.target.value as any })}
              className="w-full px-4 py-2 border border-gray-200 bg-white/80 rounded-xl shadow-sm focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-200 transition-all font-medium text-slate-700"
            >
              <option value="strict">Strict - Maximum protection</option>
              <option value="relaxed">Relaxed - Minimal filtering</option>
            </select>
          </Card>

          <Card title="Parental Controls">
            <Toggle
              title="Save Search History"
              subtitle="Keep record of searches for monitoring"
              checked={searchHistory}
              onChange={(v) => persist({ save_search_history: v })}
            />
          </Card>

          <Card title="Privacy & Data">
            <Action
              onClick={async () => {
                try {
                  setError(null);
                  setNotice(null);
                  await clearSearchHistory();
                  setNotice('Search history cleared.');
                } catch (e) {
                  console.error(e);
                  setError('Failed to clear search history');
                }
              }}
            >
              Clear Search History
            </Action>

            <Action
              onClick={async () => {
                try {
                  setError(null);
                  setNotice(null);
                  const blob = await exportSearchHistoryCsv();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'search_history.csv';
                  a.click();
                  window.URL.revokeObjectURL(url);
                  setNotice('Export started.');
                } catch (e) {
                  console.error(e);
                  setError('Failed to export data');
                }
              }}
            >
              Export My Data (CSV)
            </Action>

            <Link
              href="/report"
              className="w-full block px-4 py-3 text-left rounded-xl transition-all font-medium border text-slate-700 bg-white/60 hover:bg-white border-slate-200 shadow-sm"
            >
              Download Activity Report
            </Link>
          </Card>

          <Card title="Advanced Settings">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Blocked Keywords</label>
              <textarea
                rows={3}
                className="w-full px-4 py-3 border border-gray-200 bg-white/80 rounded-xl shadow-sm focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-200 transition-all font-medium text-slate-700"
                placeholder="Enter keywords to block, separated by commas"
                value={blockedKeywords}
                onChange={(e) => setBlockedKeywords(e.target.value)}
                onBlur={() => persist({ blocked_keywords: blockedKeywords })}
              />
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Allowed Domains</label>
              <textarea
                rows={3}
                className="w-full px-4 py-3 border border-gray-200 bg-white/80 rounded-xl shadow-sm focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-200 transition-all font-medium text-slate-700"
                placeholder="Enter trusted domains, separated by commas"
                value={allowedDomains}
                onChange={(e) => setAllowedDomains(e.target.value)}
                onBlur={() => persist({ allowed_domains: allowedDomains })}
              />
            </div>

            {saving && <p className="mt-2 text-xs font-semibold text-purple-600 animate-pulse">Saving changes...</p>}
          </Card>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white/70 backdrop-blur-xl p-6 rounded-3xl shadow-md border border-white/50 mb-6 drop-shadow-sm">
      <h3 className="text-xl font-bold text-gray-900 mb-5">{title}</h3>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function Toggle({
  title,
  subtitle,
  checked,
  onChange,
}: {
  title: string;
  subtitle: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-gray-900">{title}</p>
        <p className="text-sm text-gray-500">{subtitle}</p>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${checked ? 'bg-blue-600' : 'bg-gray-300'
          }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'
            }`}
        />
      </button>
    </div>
  );
}

function Action({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full px-4 py-2 text-left rounded-lg transition-colors border text-gray-700 hover:bg-gray-50 border-gray-200"
    >
      {children}
    </button>
  );
}
