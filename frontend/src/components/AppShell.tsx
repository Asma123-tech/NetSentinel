'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen">
      {/* App background */}
      <div className="fixed inset-0 -z-10 bg-gradient-to-b from-slate-50 via-white to-slate-50" />
      <div className="fixed inset-0 -z-10 opacity-70">
        <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-blue-200 blur-3xl" />
        <div className="absolute top-40 -right-24 h-72 w-72 rounded-full bg-violet-200 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-emerald-200 blur-3xl" />
      </div>

      <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="flex">
        <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

        <main className="flex-1 p-4 sm:p-6">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
