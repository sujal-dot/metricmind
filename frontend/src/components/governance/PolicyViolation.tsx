'use client';

import type { SecurityDecision } from '@/types/api';

interface PolicyViolationProps {
  decision: SecurityDecision | null;
  fallbackMessage?: string;
  onDismiss?: () => void;
}

function codeTone(code: string | null | undefined): {
  badge: string;
  border: string;
  bg: string;
  text: string;
} {
  switch (code) {
    case 'sql_injection':
      return {
        badge: 'bg-red-600 text-white',
        border: 'border-red-300',
        bg: 'bg-red-50',
        text: 'text-red-900',
      };
    case 'sql_request':
      return {
        badge: 'bg-amber-600 text-white',
        border: 'border-amber-300',
        bg: 'bg-amber-50',
        text: 'text-amber-900',
      };
    case 'expensive':
      return {
        badge: 'bg-orange-600 text-white',
        border: 'border-orange-300',
        bg: 'bg-orange-50',
        text: 'text-orange-900',
      };
    default:
      return {
        badge: 'bg-gray-700 text-white',
        border: 'border-gray-300',
        bg: 'bg-gray-50',
        text: 'text-gray-900',
      };
  }
}

export default function PolicyViolation({
  decision,
  fallbackMessage,
  onDismiss,
}: PolicyViolationProps) {
  if (!decision && !fallbackMessage) return null;

  const tone = codeTone(decision?.block_code ?? null);
  const reasons = decision?.matched_reasons ?? [];
  const filters = decision?.suggested_filters ?? [];
  const blockCode = decision?.block_code ?? 'unknown';
  const humanMessage = decision?.block_reason ?? fallbackMessage ?? 'This request was blocked by the security policy.';

  return (
    <div
      role="alert"
      className={`rounded-xl border-2 ${tone.border} ${tone.bg} px-4 py-4 shadow-sm`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <svg
            className={`w-6 h-6 mt-0.5 shrink-0 ${tone.text}`}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className={`text-sm font-bold uppercase tracking-wide ${tone.text}`}>
                Governance violation
              </h3>
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${tone.badge}`}>
                {blockCode}
              </span>
            </div>
            <p className={`mt-1.5 text-sm font-medium ${tone.text}`}>{humanMessage}</p>

            {reasons.length > 0 ? (
              <div className="mt-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-700 mb-1">
                  Why it was blocked
                </p>
                <ul className="list-disc pl-5 space-y-0.5 text-sm text-gray-800">
                  {reasons.slice(0, 6).map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {filters.length > 0 ? (
              <div className="mt-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-700 mb-1">
                  Try adding these filters
                </p>
                <ul className="list-disc pl-5 space-y-0.5 text-sm text-gray-800">
                  {filters.map((suggestion) => (
                    <li key={suggestion}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </div>
        {onDismiss ? (
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-md p-1 text-gray-500 hover:bg-white/60 hover:text-gray-800"
            aria-label="Dismiss warning"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        ) : null}
      </div>
    </div>
  );
}
