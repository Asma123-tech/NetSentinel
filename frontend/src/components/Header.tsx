'use client';

import Link from 'next/link';
import { Menu, X, Shield, Settings, User } from 'lucide-react';

export default function Header({
  sidebarOpen,
  setSidebarOpen,
}: {
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
}) {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/70 backdrop-blur-xl">
      <div className="px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white/70 p-2 shadow-sm hover:bg-white transition"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <Link href="/search" className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-sm">
              <Shield className="text-white" size={20} />
            </div>
            <div className="leading-tight">
              <h1 className="text-base sm:text-lg font-semibold text-slate-900">NetSentinel</h1>
              <p className="text-xs text-slate-500">Safe Search Engine</p>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/settings"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white/70 p-2 shadow-sm hover:bg-white transition"
            aria-label="Settings"
          >
            <Settings size={18} className="text-slate-700" />
          </Link>
        </div>
      </div>
    </header>
  );
}
