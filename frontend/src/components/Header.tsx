'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Menu, X, Shield, Settings, LogOut, User, LogIn } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function Header({
  sidebarOpen,
  setSidebarOpen,
}: {
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
}) {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.replace('/login');
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/40 backdrop-blur-xl">
      <div className="px-4 py-3 flex items-center justify-between">

        {/* Left: hamburger + logo */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white/70 p-2 shadow-sm hover:bg-white transition"
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <Link href="/search" className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-sm">
              <Shield className="text-white" size={20} />
            </div>
            <div className="leading-tight">
              <h1 className="text-base sm:text-lg font-semibold text-slate-900">
                NetSentinel
              </h1>
              <p className="text-xs text-slate-500">Safe Search Engine</p>
            </div>
          </Link>
        </div>

        {/* Right: context-aware actions */}
        <div className="flex items-center gap-2">

          {/* Skeleton while auth is loading */}
          {isLoading && (
            <div className="h-8 w-24 rounded-xl bg-slate-200 animate-pulse" />
          )}

          {/* ── Guest: Sign In button ── */}
          {!isLoading && !isAuthenticated && (
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white/70 px-3 py-2 shadow-sm hover:bg-white transition text-sm font-semibold text-slate-700"
            >
              <LogIn size={16} className="text-blue-600" />
              Sign In
            </Link>
          )}

          {/* ── Authenticated: username badge + settings + logout ── */}
          {!isLoading && isAuthenticated && (
            <>
              {/* Username badge — hidden on xs screens */}
              {user && (
                <div className="hidden sm:flex items-center gap-2 rounded-xl border border-slate-200 bg-white/70 px-3 py-1.5 shadow-sm">
                  <div className="h-6 w-6 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center shrink-0">
                    <User size={13} className="text-white" />
                  </div>
                  <span className="text-sm font-medium text-slate-700 max-w-[120px] truncate">
                    {user.username}
                  </span>
                </div>
              )}

              {/* Settings */}
              <Link
                href="/settings"
                className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white/70 p-2 shadow-sm hover:bg-white transition"
                aria-label="Settings"
              >
                <Settings size={18} className="text-slate-700" />
              </Link>

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white/70 p-2 shadow-sm hover:bg-rose-50 hover:border-rose-200 transition group"
                aria-label="Logout"
                title="Sign out"
              >
                <LogOut size={18} className="text-slate-700 group-hover:text-rose-600 transition" />
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
