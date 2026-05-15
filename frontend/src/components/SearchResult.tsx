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
    <div className="w-full max-w-full overflow-hidden rounded-2xl border border-gray-200 bg-white/90 p-4 sm:p-5 shadow-sm hover:shadow-md transition-shadow">

      {/* FORCE NO OVERFLOW ROOT */}
      <div className="flex flex-col gap-3 w-full min-w-0">

        {/* URL ROW */}
        <div className="flex items-center gap-2 w-full min-w-0">
          {Icon}

          <a
            href={result.url}
            target="_blank"
            rel="noreferrer"
            className="text-xs sm:text-sm text-green-700 hover:underline break-all w-full"
          >
            {result.url}
          </a>
        </div>

        {/* MAIN CONTENT */}
        <div className="flex flex-col md:flex-row gap-4 w-full min-w-0">

          {/* TEXT */}
          <div className="flex-1 min-w-0 w-full">

            <a
              href={result.url}
              target="_blank"
              rel="noreferrer"
              className="block w-full"
            >
              <h3 className="text-base sm:text-lg font-semibold text-blue-600 hover:underline break-words leading-snug">
                {result.title}
              </h3>
            </a>

            <p className="mt-2 text-sm sm:text-base text-gray-700 leading-relaxed break-words w-full">
              {result.snippet}
            </p>
          </div>

          {/* IMAGE */}
          {thumbSrc && (
            <div className="w-full md:w-36 flex-shrink-0">
              <div className="w-full h-40 sm:h-32 md:h-24 overflow-hidden rounded-xl border border-gray-200">
                <img
                  src={thumbSrc}
                  alt={result.title}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>

              <div className="mt-2 flex md:justify-end">
                <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800">
                  <Shield size={12} className="mr-1" />
                  Safe
                </span>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}