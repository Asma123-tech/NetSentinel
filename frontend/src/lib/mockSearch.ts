// src/lib/mockSearch.ts
import type { SearchResult } from '@/types';

export async function mockSearch(query: string): Promise<SearchResult[]> {
  await new Promise((r) => setTimeout(r, 800));
  if (!query.trim()) return [];
  const now = new Date().toISOString();

  return [
    {
      id: 1,
      title: 'Sample Safe Search Result 1',
      url: 'https://example.com/page1',
      snippet: 'This is a safe and filtered search result that matches your query...',
      type: 'text',
      timestamp: now,
    },
    {
      id: 2,
      title: 'Educational Content Example',
      url: 'https://example.com/page2',
      snippet: 'Educational and family-friendly content verified by NetSentinel AI...',
      type: 'text',
      timestamp: now,
    },
  ];
}
