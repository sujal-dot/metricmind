'use client';

import { useState } from 'react';
import type { CubeTrace } from '@/types/api';
import APIModal from './APIModal';

interface ViewAPIButtonProps {
  trace: CubeTrace | null | undefined;
  className?: string;
}

export default function ViewAPIButton({ trace, className }: ViewAPIButtonProps) {
  const [open, setOpen] = useState(false);
  const disabled = !trace;

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
            d="M3 6h18M3 12h18M3 18h18" />
        </svg>
        View API
      </button>
      <APIModal open={open} onClose={() => setOpen(false)} trace={trace ?? null} />
    </>
  );
}
