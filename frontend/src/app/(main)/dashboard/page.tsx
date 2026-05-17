'use client';

import Link from 'next/link';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useEffect, useMemo, useState } from 'react';
import { Search, Shield, Clock, ArrowUpRight, Activity } from 'lucide-react';
import {
  fetchOverviewStats,
  fetchRecentActivity,
  exportSearchHistoryCsv,
  type OverviewStats,
  type ActivityItem,
} from '@/lib/api';

function StatCard({
  label,
  value,
  icon: Icon,
  hint,
}: {
  label: string;
  value: string;
  icon: any;
  hint?: string;
}) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white/70 backdrop-blur-xl p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="absolute -right-10 -top-10 h-24 w-24 rounded-full bg-gradient-to-br from-blue-200 to-violet-200 blur-2xl opacity-70" />

      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-sm">
            <Icon size={18} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-700">{label}</p>
            {hint && <p className="text-xs text-slate-500">{hint}</p>}
          </div>
        </div>

        <div className="text-3xl font-semibold tracking-tight text-slate-900">{value}</div>
      </div>
    </div>
  );
}

function Panel({
  title,
  icon: Icon,
  children,
  right,
}: {
  title: string;
  icon: any;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/70 backdrop-blur-xl shadow-sm">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200/70">
        <div className="flex items-center gap-2">
          <Icon size={18} className="text-slate-700" />
          <h3 className="font-semibold text-slate-900">{title}</h3>
        </div>
        {right}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function SkeletonLine() {
  return <div className="h-4 w-full animate-pulse rounded-full bg-slate-200" />;
}

async function downloadCsv(setError: (v: string | null) => void) {
  try {
    setError(null);
    const blob = await exportSearchHistoryCsv();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'search_history.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    console.error(e);
    setError('Failed to export data');
  }
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [recent, setRecent] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [o, r] = await Promise.all([fetchOverviewStats(), fetchRecentActivity(5)]);
        if (!mounted) return;
        setOverview(o);
        setRecent(r);
      } catch (err) {
        console.error(err);
        if (mounted) setError('Failed to load stats');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const cards = useMemo(() => {
    if (!overview) return [];
    return [
      { label: 'Total Searches', value: overview.total_searches.toString(), icon: Search, hint: 'All-time queries' },
      { label: 'Blocked Content', value: overview.blocked_content.toString(), icon: Shield, hint: 'Filtered results' },
      { label: 'Safe Results', value: overview.safe_results.toString(), icon: Shield, hint: 'Allowed results' },
      { label: 'Active Time', value: `${overview.active_time_hours}h`, icon: Clock, hint: 'Time protected' },
    ];
  }, [overview]);

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

        <div className="relative z-10 px-4 py-8 max-w-7xl mx-auto border-none">
          {/* Header */}
          <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">Dashboard</h2>
              <p className="text-sm text-slate-600">Overview of your protection and recent searches.</p>
            </div>
            <div className="flex gap-2">
              <Link
                href="/report"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white/70 px-4 py-2 text-sm text-slate-700 shadow-sm hover:bg-white transition"
              >
                View report <ArrowUpRight size={16} />
              </Link>
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Stats */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="rounded-2xl border border-slate-200 bg-white/70 p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <div className="h-10 w-10 rounded-2xl bg-slate-200 animate-pulse" />
                    <div className="h-8 w-16 rounded-lg bg-slate-200 animate-pulse" />
                  </div>
                  <SkeletonLine />
                  <div className="mt-2 w-2/3">
                    <SkeletonLine />
                  </div>
                </div>
              ))}
            </div>
          ) : overview ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {cards.map((s, i) => (
                <StatCard key={i} label={s.label} value={s.value} icon={s.icon} hint={s.hint} />
              ))}
            </div>
          ) : null}

          {/* Panels */}
          {!loading && overview && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <Panel
                  title="Recent Activity"
                  icon={Activity}
                  right={<span className="text-xs text-slate-500">{recent.length} items</span>}
                >
                  <div className="space-y-3">
                    {recent.length === 0 ? (
                      <div className="rounded-xl border border-slate-200 bg-white/60 p-4 text-sm text-slate-600">
                        No recent searches yet.
                      </div>
                    ) : (
                      recent.map((item) => (
                        <div
                          key={item.id}
                          className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 rounded-xl border border-slate-200 bg-white/60 px-4 py-3"
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-sm">
                              <Search size={16} className="text-white" />
                            </div>
                            <div className="min-w-0">
                              <p className="truncate font-medium text-slate-900">{item.query}</p>
                              <p className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 border border-emerald-200">
                              Safe: {item.safe_results}
                            </span>
                            <span className="inline-flex items-center rounded-full bg-rose-50 px-3 py-1 text-xs font-medium text-rose-700 border border-rose-200">
                              Blocked: {item.blocked_results}
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </Panel>
              </div>

              <div className="space-y-4">
                <Panel title="Content Filtering Stats" icon={Shield}>
                  <MiniRow label="Filtered Items (total)" value={overview.blocked_content.toString()} />
                  <MiniRow label="Safe Results (total)" value={overview.safe_results.toString()} />
                  <MiniRow label="Searches (total)" value={overview.total_searches.toString()} />
                </Panel>

                <Panel title="Quick Actions" icon={ArrowUpRight}>
                  <Link
                    href="/report"
                    className="w-full rounded-xl border border-slate-200 bg-white/70 px-4 py-2 text-left text-sm text-slate-700 hover:bg-white transition block"
                  >
                    View Full Report
                  </Link>

                  <button
                    onClick={() => downloadCsv(setError)}
                    className="w-full rounded-xl border border-slate-200 bg-white/70 px-4 py-2 text-left text-sm text-slate-700 hover:bg-white transition"
                  >
                    Export Data (CSV)
                  </button>

                  <Link
                    href="/settings"
                    className="w-full rounded-xl border border-slate-200 bg-white/70 px-4 py-2 text-left text-sm text-slate-700 hover:bg-white transition block"
                  >
                    Configure Alerts
                  </Link>
                </Panel>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}

function MiniRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white/60 px-4 py-3">
      <span className="text-sm text-slate-600">{label}</span>
      <span className="text-sm font-semibold text-slate-900">{value}</span>
    </div>
  );
}
