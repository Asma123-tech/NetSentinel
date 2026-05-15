'use client';

import { useMemo, useState } from 'react';
import {
  Search,
  Filter,
  Shield,
  Image as ImageIcon,
  List,
  Sparkles,
  X,
  Zap,
  Eye,
  Lock,
} from 'lucide-react';

import { useSearchSettings } from '@/context/SearchSettingsContext';
import type { SearchResult } from '@/types';
import SearchResultCard from '@/components/SearchResult';
import { performSearch, type FilterMode } from '@/lib/api';


// ---------------- THEME COLORS ----------------
const THEME = {
  primary: 'from-pink-500 to-purple-600',       // search button gradient
  icon: 'from-pink-500 to-purple-600',         // feature card icons gradient
  heading: 'bg-gradient-to-r from-pink-500 to-purple-600 text-transparent bg-clip-text', // NetSentinel heading gradient
};

type Tab = 'all' | 'images';
const PAGE_SIZE_ALL = 20;
const PAGE_SIZE_IMAGES = 80;

function ModePill({ mode }: { mode: FilterMode }) {
  const styles =
    mode === 'strict'
      ? 'border-rose-200 bg-rose-50 text-rose-700'
      : mode === 'moderate'
        ? 'border-amber-200 bg-amber-50 text-amber-700'
        : 'border-emerald-200 bg-emerald-50 text-emerald-700';

  const label =
    mode === 'strict' ? 'Strict' : mode === 'moderate' ? 'Moderate' : 'Relaxed';

  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${styles}`}>
      <Shield size={14} />
      {label} Mode
    </span>
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/70 p-5 shadow-sm">
      <div className="h-4 w-2/3 bg-slate-200 animate-pulse rounded-full" />
      <div className="mt-3 h-6 w-1/2 bg-slate-200 animate-pulse rounded-lg" />
      <div className="mt-3 space-y-2">
        <div className="h-4 w-full bg-slate-200 animate-pulse rounded-full" />
        <div className="h-4 w-11/12 bg-slate-200 animate-pulse rounded-full" />
        <div className="h-4 w-2/3 bg-slate-200 animate-pulse rounded-full" />
      </div>
    </div>
  );
}


function FeatureCard({
  icon: Icon,
  title,
  desc,
}: {
  icon: any;
  title: string;
  desc: string;
}) {
  return (
    <div className="group flex items-center gap-4 rounded-2xl bg-white/80 p-4 shadow-lg backdrop-blur-md transition-all hover:shadow-2xl hover:-translate-y-1 w-full max-w-5xl">
      <div className={`p-3 rounded-xl bg-gradient-to-r ${THEME.icon} text-white`}>
        <Icon size={28} />
      </div>
      <div>
        <h3 className="text-lg font-bold text-slate-800">{title}</h3>
        <p className="text-sm leading-relaxed text-slate-600">{desc}</p>
      </div>
    </div>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('all');
  const [selectedImage, setSelectedImage] = useState<SearchResult | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const { filterMode, setFilterMode } = useSearchSettings();
  const showWelcome = results.length === 0 && !isSearching && !query;

  const imageResults = useMemo(() => results.filter((r) => r.preview_url), [results]);

  const showSpinner = isSearching && !isLoadingMore;

  const modeLabel =
    filterMode === 'strict'
      ? 'Adult sites filtered, nude images blurred.'
      : 'Everything searchable, images unblurred. Use responsibly.';

  const runSearch = async (
    newPage: number = 1,
    tab: Tab = activeTab,
    mode: FilterMode = filterMode
  ) => {
    if (!query.trim()) return;

    const size = tab === 'images' ? PAGE_SIZE_IMAGES : PAGE_SIZE_ALL;
    const limit = newPage * size;

    try {
      if (newPage === 1) {
        setIsSearching(true);
        setError(null);
      } else {
        setIsLoadingMore(true);
      }

      const { results: data, has_more } = await performSearch(query, mode, limit);

      setResults(data);
      setPage(newPage);
      setHasMore(has_more);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || 'Search failed');
      setResults([]);
      setHasMore(false);
    } finally {
      setIsSearching(false);
      setIsLoadingMore(false);
    }
  };

  const handleSearch = () => {
    if (!query.trim()) return;
    setHasSearched(true);   // ✅ Mark that search was performed
    setSelectedImage(null);
    setResults([]);
    setPage(1);
    setHasMore(false);
    runSearch(1, activeTab, filterMode);
  };

  const handleLoadMore = () => {
    if (!hasMore || isSearching || isLoadingMore) return;
    runSearch(page + 1, activeTab, filterMode);
  };

  const handleFilterChange = (value: FilterMode) => {
    if (value === filterMode) return;

    setFilterMode(value);

    if (query.trim()) {
      setSelectedImage(null);
      setResults([]);
      setPage(1);
      setHasMore(false);
      runSearch(1, activeTab, value);
    }
  };

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    setSelectedImage(null);
    if (!query.trim()) return;
    setResults([]);
    setPage(1);
    setHasMore(false);
    runSearch(1, tab, filterMode);
  };

  const getImageSrc = (preview_url?: string) => {
    if (!preview_url) return '';
    const separator = preview_url.includes('?') ? '&' : '?';
    return `${preview_url}${separator}mode=${filterMode}`;
  };


  return (
    <div className="relative min-h-screen pt-10 pb-20 px-3 sm:px-6 overflow-x-hidden">
      {/* FULL BACKGROUND IMAGE */}
      <div
        className="fixed inset-0 -z-[5] bg-cover bg-center pointer-events-none blur-md scale-105"
        style={{ backgroundImage: "url('/images/1.jpg')" }}
      />

      {/* FLOATING BACKGROUND IMAGES – only show on welcome */}
      {showWelcome && (
        <>
          <div className="fixed animate-float-slow top-48 sm:top-32 left-2 sm:left-20 w-16 sm:w-28" style={{ mixBlendMode: 'multiply' }}>
            <img src="/images/float1.png" alt="float1" />
          </div>
          <div className="fixed animate-float-slow top-48 sm:top-32 right-2 sm:right-20 w-16 sm:w-28" style={{ mixBlendMode: 'multiply' }}>
            <img src="/images/float4.png" alt="float2" />
          </div>
        </>
      )}

      {/* HEADING */}
      <div className={`relative z-20 text-center transition-all duration-500 ${showWelcome ? '-mt-4' : '-mt-12'}`}>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-black drop-shadow-[0_2px_8px_rgba(255,255,255,0.6)]">
          NetSentinel
        </h1>
        <p className="text-black/80 font-medium mt-1">
          Safe Search Engine
        </p>
      </div>

      {/* SEARCH BAR */}
      <div className={`relative z-10 mx-auto max-w-5xl transition-all duration-500 ${showWelcome ? 'mt-16' : 'mt-8'}`}>
        <div className="relative w-full">
          <Search
            className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            size={20}
          />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setHasSearched(false);
            }}
            onKeyDown={(e) => e.key === 'Enter' && runSearch()}
            placeholder="Search the web freely and safely..."
            className="w-full min-w-0 rounded-3xl border border-slate-300/50 bg-white/50 pl-12 pr-32 sm:pr-40 py-3 text-sm sm:text-lg text-slate-900 font-medium shadow-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-300 overflow-x-auto"
          />
          <button
            onClick={handleSearch}
            className={`absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2 rounded-2xl bg-gradient-to-r ${THEME.primary} px-3 sm:px-5 py-2 text-sm sm:text-lg font-semibold shadow-md hover:scale-105 hover:shadow-lg transition-all duration-200`}
          >
            <Sparkles size={16} />
            Search
          </button>
        </div>
      </div>
      {/* WHY NETSENTINEL BOX */}
      {showWelcome && (
        <div className="relative max-w-5xl mx-auto bg-white/70 backdrop-blur-md rounded-3xl p-4 shadow-xl mt-8 transition-opacity duration-500">
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">

            {/* Owl + title inline on mobile / owl alone on desktop */}
            <div className="flex items-center gap-3 md:block flex-shrink-0">
              <img
                src="/images/why-image (1).png"
                alt="Why NetSentinel"
                className="w-20 md:w-52 object-contain drop-shadow-2xl"
              />
              <h2 className="text-lg font-bold text-black leading-tight md:hidden">Why NetSentinel?</h2>
            </div>

            {/* Title above text on desktop / just text on mobile */}
            <div className="flex-1">
              <h2 className="hidden md:block text-3xl font-bold text-black mb-2">Why NetSentinel?</h2>
              <p className="text-slate-700 leading-relaxed text-sm md:text-lg max-w-2xl">
                NetSentinel is a secure search environment designed for your kids to protect
                them from harmful content. Leveraging real-time filtering algorithms and customizable
                safety protocols, it ensures a safe browsing experience for educational and professional use.
              </p>
            </div>

          </div>
        </div>
      )}

      {/* FEATURE CARDS */}
      {showWelcome && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 max-w-5xl mx-auto transition-opacity duration-500">
          <FeatureCard
            icon={Shield}
            title="Privacy First"
            desc="Your searches are private and never tracked. We ensure your data stays safe online at all times. Enjoy a worry-free browsing experience without sharing sensitive information."
          />
          <FeatureCard
            icon={Eye}
            title="Clarity & Focus"
            desc="Get direct answers without clutter. Stay focused on what matters most while browsing the web. Our streamlined interface reduces distractions and helps you find the information you need quickly."
          />
          <FeatureCard
            icon={Lock}
            title="Safe Browsing"
            desc="Protected from harmful content and unsafe websites. NetSentinel ensures a safer search experience for you and your family online."
          />
          <FeatureCard
            icon={Sparkles}
            title="Kids Zone"
            desc="Special designed for kids with safe and fun content. Explore educational and entertaining material online, designed to keep children engaged, curious, and protected at all times"
          />
        </div>
      )}

      {/* Tabs */}
      {!showWelcome && (
        <div className="flex justify-center mt-8">
          <div className="inline-flex w-fit rounded-2xl border border-slate-200 bg-white/70 p-1 shadow-sm">
            <button
              onClick={() => handleTabChange('all')}
              className={[
                'flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition',
                activeTab === 'all'
                  ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-sm'
                  : 'text-slate-700 hover:bg-white',
              ].join(' ')}
            >
              <List size={16} />
              All
            </button>

            <button
              onClick={() => handleTabChange('images')}
              className={[
                'flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition',
                activeTab === 'images'
                  ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-sm'
                  : 'text-slate-700 hover:bg-white',
              ].join(' ')}
            >
              <ImageIcon size={16} />
              Images
            </button>
          </div>
        </div>
      )}

      {/* Loading */}
      {showSpinner && (
        <div className="grid grid-cols-1 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {/* Error */}
      {!showSpinner && error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {/* No results */}
      {!showSpinner && !error && hasSearched && results.length === 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white/70 p-8 text-center shadow-sm">
          <p className="text-slate-700 font-medium">No results found</p>
          <p className="mt-1 text-sm text-slate-500">Try different keywords or switch the filter mode.</p>
        </div>
      )}

      {/* ALL RESULTS TAB */}
      {!showSpinner && !error && results.length > 0 && activeTab === 'all' && (
        <>
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Showing {results.length} result{results.length !== 1 && 's'}
              {hasMore && ' (more available)'}
            </p>
          </div>

          <div className="space-y-4">
            {results.map((r) => (
              <SearchResultCard key={r.id} result={r} />
            ))}
          </div>

          <div className="flex justify-center mt-6">
            {hasMore && (
              <button
                onClick={handleLoadMore}
                disabled={isLoadingMore}
                className="rounded-xl border border-slate-200 bg-white/70 px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-white transition disabled:opacity-60"
              >
                {isLoadingMore ? 'Loading more…' : 'Load more results'}
              </button>
            )}
          </div>
        </>
      )}

      {/* IMAGES TAB */}
      {!showSpinner && !error && activeTab === 'images' && (
        <>
          {imageResults.length === 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-white/70 p-8 text-center shadow-sm">
              <p className="text-slate-700 font-medium">No image results</p>
              <p className="mt-1 text-sm text-slate-500">Try another query or switch modes.</p>
            </div>
          ) : (
            <>
              <p className="text-xs text-slate-500 mb-2">
                Showing {imageResults.length} image result
                {imageResults.length !== 1 && 's'}
                {hasMore && ' (more available)'}
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {imageResults.map((r) => (
                  <button
                    key={r.id}
                    className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white/70 shadow-sm hover:shadow-md transition"
                    onClick={() => setSelectedImage(r)}
                  >
                    <img
                      src={getImageSrc(r.preview_url)}
                      alt={r.title}
                      className="w-full h-44 object-cover group-hover:scale-[1.03] transition-transform duration-200"
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.closest('button')?.classList.add('hidden');
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/35 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="absolute bottom-0 left-0 right-0 p-3 text-left opacity-0 group-hover:opacity-100 transition-opacity">
                      <p className="text-xs text-white line-clamp-2">{r.title}</p>
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex justify-center mt-6">
                {hasMore && (
                  <button
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                    className="rounded-xl border border-slate-200 bg-white/70 px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-white transition disabled:opacity-60"
                  >
                    {isLoadingMore ? 'Loading more images…' : 'Load more images'}
                  </button>
                )}
              </div>
            </>
          )}
        </>
      )}

      {/* Lightbox */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="relative w-full max-w-5xl max-h-[85vh] overflow-hidden rounded-2xl bg-black shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-3 right-3 z-10 rounded-full bg-white/10 px-3 py-1.5 text-xs text-white backdrop-blur hover:bg-white/20 transition"
              onClick={() => setSelectedImage(null)}
            >
              Close
            </button>

            <img
              src={getImageSrc(selectedImage.preview_url)}
              alt={selectedImage.title}
              className="max-w-full max-h-[85vh] object-contain mx-auto"
            />

            <div className="px-4 py-3 text-xs text-slate-200 bg-black/60 flex items-center justify-between gap-3">
              <span className="truncate">{selectedImage.title}</span>
              <a
                href={selectedImage.url}
                target="_blank"
                rel="noreferrer"
                className="underline whitespace-nowrap"
              >
                Open source page
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}