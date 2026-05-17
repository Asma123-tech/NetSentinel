'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { usePathname } from 'next/navigation';
import { Search, BarChart3, Settings, HelpCircle, LogOut, LogIn } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const NAV_ITEMS = [
  { href: '/search',    icon: Search,    label: 'Search' },
  { href: '/dashboard', icon: BarChart3, label: 'Dashboard' },
  { href: '/settings',  icon: Settings,  label: 'Settings' },
  { href: '/help',      icon: HelpCircle,label: 'Help' },
];

export default function Sidebar({
  sidebarOpen,
  setSidebarOpen,
}: {
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
}) {
  const pathname             = usePathname();
  const { logout, isAuthenticated } = useAuth();
  const router               = useRouter();

  const handleLogout = () => {
    setSidebarOpen(false);
    logout();
    router.replace('/login');
  };

  return (
    <>
      <aside
        className={`fixed left-0 top-[57px] h-[calc(100vh-57px)] w-64 z-30
          border-r border-slate-200/70 bg-white/70 backdrop-blur-xl
          transform transition-transform duration-200 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex flex-col h-full p-4">

          {/* Navigation label */}
          <div className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
            Navigation
          </div>

          {/* Nav links */}
          <nav className="space-y-1">
            {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setSidebarOpen(false)}
                  className={[
                    'group relative flex items-center gap-3 rounded-xl px-4 py-3 transition',
                    active
                      ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-sm'
                      : 'text-slate-700 hover:bg-white/80',
                  ].join(' ')}
                >
                  <Icon
                    size={18}
                    className={
                      active
                        ? 'text-white'
                        : 'text-slate-600 group-hover:text-slate-800'
                    }
                  />
                  <span className="font-medium">{label}</span>
                  {active && (
                    <span className="absolute inset-0 rounded-xl ring-1 ring-white/20" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Tip card */}
          <div className="mt-6 rounded-2xl border border-slate-200 bg-white/60 p-4">
            <p className="text-sm font-bold text-red-600">Tip</p>
            <p className="mt-1 text-xs text-slate-600">
              Use{' '}
              <span className="font-bold text-red-600">Strict</span> mode for
              safer browsing.
            </p>
          </div>

          {/* Bottom: Sign In (guest) or Logout (authenticated) */}
          <div className="mt-auto pt-4 border-t border-slate-200/70">
            {isAuthenticated ? (
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 rounded-xl px-4 py-3 text-rose-600 hover:bg-rose-50 transition font-medium"
              >
                <LogOut size={18} />
                Sign Out
              </button>
            ) : (
              <Link
                href="/login"
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-3 rounded-xl px-4 py-3 text-blue-600 hover:bg-blue-50 transition font-medium"
              >
                <LogIn size={18} />
                Sign In
              </Link>
            )}
          </div>
        </div>
      </aside>

      {/* Backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </>
  );
}
