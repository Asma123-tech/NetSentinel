'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { fetchOverviewStats, fetchRecentActivity, type OverviewStats, type ActivityItem } from '@/lib/api';

export default function ReportPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [recent, setRecent] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [o, r] = await Promise.all([fetchOverviewStats(), fetchRecentActivity(25)]);
        if (!mounted) return;
        setOverview(o);
        setRecent(r);
      } catch (e) {
        console.error(e);
        if (mounted) setError('Failed to load report');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <div className="p-6 text-slate-600">Loading report...</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Activity Report</h2>
          <p className="text-sm text-slate-600">Summary of searches and filtering.</p>
        </div>

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white/70 px-4 py-2 text-sm text-slate-700 shadow-sm hover:bg-white transition"
        >
          <ArrowLeft size={16} /> Back
        </Link>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {overview && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
            <Stat label="Total Searches" value={overview.total_searches} />
            <Stat label="Blocked Content" value={overview.blocked_content} />
            <Stat label="Safe Results" value={overview.safe_results} />
            <Stat label="Active Time (hrs)" value={overview.active_time_hours} />
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white/70 p-5">
            <h3 className="font-semibold text-slate-900 mb-3">Recent Searches</h3>
            <div className="space-y-2">
              {recent.length === 0 ? (
                <div className="text-sm text-slate-600">No history found.</div>
              ) : (
                recent.map((x) => (
                  <div
                    key={x.id}
                    className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white/60 px-4 py-3"
                  >
                    <div className="min-w-0">
                      <div className="font-medium text-slate-900 truncate">{x.query}</div>
                      <div className="text-xs text-slate-500">{new Date(x.created_at).toLocaleString()}</div>
                    </div>

                    <div className="flex gap-2 shrink-0">
                      <span className="text-xs rounded-full border px-3 py-1 bg-emerald-50 border-emerald-200 text-emerald-700">
                        Safe: {x.safe_results}
                      </span>
                      <span className="text-xs rounded-full border px-3 py-1 bg-rose-50 border-rose-200 text-rose-700">
                        Blocked: {x.blocked_results}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/70 p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-2xl font-semibold text-slate-900">{value}</div>
    </div>
  );
}
