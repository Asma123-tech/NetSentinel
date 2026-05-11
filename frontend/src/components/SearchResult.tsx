// src/components/SearchResult.tsx
'use client';

import { Shield, Image as ImageIcon, Video, FileText } from 'lucide-react';
import type { SearchResult } from '@/types';
import { useSearchSettings } from '@/context/SearchSettingsContext';

export default function SearchResultCard({ result }: { result: SearchResult }) {
  const { filterMode } = useSearchSettings();

  const Icon =
    result.type === 'image' ? (
      <ImageIcon size={16} className="text-purple-600" />
    ) : result.type === 'video' ? (
      <Video size={16} className="text-red-600" />
    ) : (
      <FileText size={16} className="text-blue-600" />
    );

  const thumbSrc = result.preview_url
    ? `${result.preview_url}${result.preview_url.includes('?') ? '&' : '?'}mode=${filterMode}`
    : undefined;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {Icon}
            <a
              href={result.url}
              className="text-sm text-green-700 hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              {result.url}
            </a>
          </div>
          <a href={result.url} className="block" target="_blank" rel="noreferrer">
            <h3 className="text-xl text-blue-600 hover:underline cursor-pointer mb-2">
              {result.title}
            </h3>
          </a>
          <p className="text-gray-700 leading-relaxed">{result.snippet}</p>
        </div>

        <div className="flex flex-col items-end gap-2">
          {thumbSrc && (
            <div className="w-32 h-20 overflow-hidden rounded-md border border-gray-200">
              <img
                src={thumbSrc}
                alt={result.title}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            </div>
          )}
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <Shield size={12} className="mr-1" /> Safe
          </span>
        </div>
      </div>
    </div>
  );
}
