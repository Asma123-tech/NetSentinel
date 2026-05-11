// src/lib/api.ts
'use client';

import type { SearchResult } from '@/types';

const API_BASE_URL =
  (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');

export type FilterMode = 'strict' | 'moderate' | 'relaxed';

export type BackendSettings = {
  filter_mode: FilterMode;
  parental_controls: boolean;
  notifications: boolean;
  save_search_history: boolean;
  blocked_keywords: string;
  allowed_domains: string;
};

export type OverviewStats = {
  total_searches: number;
  blocked_content: number;
  safe_results: number;
  active_time_hours: number;
};

export type ActivityItem = {
  id: number;
  query: string;
  created_at: string;
  safe_results: number;
  blocked_results: number;
};

async function handleJsonResponse(res: Response) {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API error ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

// --- SEARCH ---
export type SearchApiResponse = {
  results: SearchResult[];
  has_more: boolean;
};

export async function performSearch(
  query: string,
  filterMode?: FilterMode,
  limit = 30
): Promise<SearchApiResponse> {
  const res = await fetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit, filter_mode: filterMode }),
  });

  const data = await handleJsonResponse(res);

  return {
    has_more: data.has_more,
    results: (data.results as any[]).map((item) => ({
      id: item.id,
      title: item.title,
      url: item.url,
      snippet: item.snippet,
      type: item.type,
      timestamp: item.timestamp,
      preview_url: item.preview_url ? `${API_BASE_URL}${item.preview_url}` : undefined,
    })),
  };
}

// --- SETTINGS ---

export async function fetchSettings(): Promise<BackendSettings> {
  const res = await fetch(`${API_BASE_URL}/api/settings`);
  return handleJsonResponse(res);
}

export async function updateSettings(payload: Partial<BackendSettings>): Promise<BackendSettings> {
  const res = await fetch(`${API_BASE_URL}/api/settings`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleJsonResponse(res);
}

// --- STATS ---

export async function fetchOverviewStats(): Promise<OverviewStats> {
  const res = await fetch(`${API_BASE_URL}/api/stats/overview`);
  return handleJsonResponse(res);
}

export async function fetchRecentActivity(limit = 10): Promise<ActivityItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/stats/recent?limit=${encodeURIComponent(String(limit))}`);
  return handleJsonResponse(res);
}

// --- HISTORY (NEW) ---

export async function clearSearchHistory(): Promise<{ ok: boolean; deleted_queries?: number }> {
  const res = await fetch(`${API_BASE_URL}/api/history`, { method: 'DELETE' });
  return handleJsonResponse(res);
}


export async function exportSearchHistoryCsv(): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}/api/history/export.csv`, { method: 'GET' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Export failed ${res.status}: ${text || res.statusText}`);
  }
  return res.blob();
}
