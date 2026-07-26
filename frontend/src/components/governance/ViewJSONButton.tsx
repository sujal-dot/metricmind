'use client';

import { useState } from 'react';
import type { JsonValue } from '@/types/api';
import JSONViewer from './JSONViewer';

interface ViewJSONButtonProps {
  data: JsonValue | null | undefined;
  title?: string;
  className?: string;
}

export default function ViewJSONButton({ data, title, className }: ViewJSONButtonProps) {
  const [open, setOpen] = useState(false);
  const disabled = data === null || data === undefined || (typeof data === 'object' && !Array.isArray(data) && Object.keys(data as Record<string, unknown>).length === 0);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={disabled}
        className={`inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed ${
          className ?? ''
        }`}
      >
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        View JSON
      </button>
      <JSONViewer
        open={open}
        onClose={() => setOpen(false)}
        data={data ?? null}
        title={title}
      />
    </>
  );
}
