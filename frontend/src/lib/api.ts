import type { SearchResult } from '@/types';
import { API_BASE_URL } from '@/lib/config';
import { getStoredToken } from '@/lib/tokenstorage';

export { API_BASE_URL };

// ── Authenticated fetch ────────────────────────────────────────
// Attaches the Bearer token from localStorage to every request.
function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  const headers: HeadersInit = {
    ...(init.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  return fetch(input, { ...init, headers });
}

async function handleJsonResponse(res: Response) {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API error ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

// ── Types ──────────────────────────────────────────────────────

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

export type SearchApiResponse = {
  results: SearchResult[];
  has_more: boolean;
};

// ── Search ─────────────────────────────────────────────────────

export async function performSearch(
  query: string,
  filterMode?: FilterMode,
  limit = 30,
  page = 1,
  categories?: string,
): Promise<SearchApiResponse> {
  const res = await authFetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit, filter_mode: filterMode, page, categories }),
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
      preview_url: item.preview_url
        ? `${API_BASE_URL}${item.preview_url}`
        : undefined,
    })),
  };
}

// ── Settings ───────────────────────────────────────────────────

export async function fetchSettings(): Promise<BackendSettings> {
  const res = await authFetch(`${API_BASE_URL}/api/settings`);
  return handleJsonResponse(res);
}

export async function updateSettings(
  payload: Partial<BackendSettings>,
): Promise<BackendSettings> {
  const res = await authFetch(`${API_BASE_URL}/api/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleJsonResponse(res);
}

// ── Stats ──────────────────────────────────────────────────────

export async function fetchOverviewStats(): Promise<OverviewStats> {
  const res = await authFetch(`${API_BASE_URL}/api/stats/overview`);
  return handleJsonResponse(res);
}

export async function fetchRecentActivity(limit = 10): Promise<ActivityItem[]> {
  const res = await authFetch(
    `${API_BASE_URL}/api/stats/recent?limit=${encodeURIComponent(String(limit))}`,
  );
  return handleJsonResponse(res);
}

// ── History ────────────────────────────────────────────────────

export async function clearSearchHistory(): Promise<{
  ok: boolean;
  deleted_queries?: number;
}> {
  const res = await authFetch(`${API_BASE_URL}/api/history`, {
    method: 'DELETE',
  });
  return handleJsonResponse(res);
}

export async function exportSearchHistoryCsv(): Promise<Blob> {
  const res = await authFetch(`${API_BASE_URL}/api/history/export.csv`);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Export failed ${res.status}: ${text || res.statusText}`);
  }
  return res.blob();
}