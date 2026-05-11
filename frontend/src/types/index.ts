// src/types/index.ts
export type ResultType = 'text' | 'image' | 'video';

export type SearchResult = {
  id: number;
  title: string;
  url: string;
  snippet: string;
  type: ResultType;
  timestamp: string;
  preview_url?: string; // NEW
};
