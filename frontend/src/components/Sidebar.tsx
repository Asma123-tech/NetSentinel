'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Search, BarChart3, Settings, User, HelpCircle } from 'lucide-react';

const items = [
  { href: '/search', icon: Search, label: 'Search' },
  { href: '/dashboard', icon: BarChart3, label: 'Dashboard' },
  { href: '/settings', icon: Settings, label: 'Settings' },
  { href: '/help', icon: HelpCircle, label: 'Help' },
];

export default function Sidebar({
  sidebarOpen,
  setSidebarOpen,
}: {
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
}) {
  const pathname = usePathname();

  return (
    <>
      <aside
        className={`fixed left-0 top-[57px] h-[calc(100vh-57px)] w-64 transform transition-transform duration-200 ease-in-out z-30
          border-r border-slate-200/70 bg-white/70 backdrop-blur-xl
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="p-4">
          <div className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
            Navigation
          </div>

          <nav className="space-y-1">
            {items.map(({ href, icon: Icon, label }) => {
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
                  <Icon size={18} className={active ? 'text-white' : 'text-slate-600 group-hover:text-slate-800'} />
                  <span className="font-medium">{label}</span>
                  {active && <span className="absolute inset-0 rounded-xl ring-1 ring-white/20" />}
                </Link>
              );
            })}
          </nav>

         <div className="mt-6 rounded-2xl border border-slate-200 bg-white/60 p-4">
  <p className="text-sm font-bold text-red-600 hover:text-red-700 transition-colors duration-200 cursor-pointer">
    Tip
  </p>
  <p className="mt-1 text-xs text-slate-600">
    Use{" "}
    <span className="font-bold text-red-600 hover:text-red-700 transition-colors duration-200 cursor-pointer">
      Strict
    </span>{" "}
    mode for safer browsing.
  </p>
</div>

        </div>
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </>
  );
}
