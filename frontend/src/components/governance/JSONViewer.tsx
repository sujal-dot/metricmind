'use client';

import { useMemo, useState } from 'react';
import type { JsonValue } from '@/types/api';

interface JSONViewerProps {
  open: boolean;
  onClose: () => void;
  data: JsonValue | null | undefined;
  title?: string;
}

export default function JSONViewer({ open, onClose, data, title }: JSONViewerProps) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(true);

  const pretty = useMemo(() => {
    if (data === null || data === undefined) return '{}';
    try {
      return JSON.stringify(data as unknown as Record<string, unknown>, null, 2);
    } catch {
      return String(data);
    }
  }, [data]);

  if (!open) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(pretty);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Raw Cube API JSON response"
    >
      <div
        className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-xl bg-white shadow-2xl flex flex-col"
        onClick={(evt) => evt.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {title ?? 'View JSON — Cube.dev Response'}
            </h3>
            <p className="text-sm text-gray-500 mt-0.5 truncate">
              Pretty-printed Cube API JSON — exactly what MetricMind received from the semantic layer
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setExpanded((prev) => !prev)}
              className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {expanded ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                )}
              </svg>
              {expanded ? 'Collapse' : 'Expand'}
            </button>
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              {copied ? 'Copied!' : 'Copy to clipboard'}
            </button>
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-800"
              aria-label="Close JSON viewer"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className={`overflow-auto px-6 py-5 ${expanded ? '' : 'max-h-48'}`}>
          <pre className="font-mono text-xs text-gray-800 bg-gray-50 border border-gray-200 rounded-md p-4 whitespace-pre-wrap break-all">
{pretty}
          </pre>
        </div>
      </div>
    </div>
  );
}
