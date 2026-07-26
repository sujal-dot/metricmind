'use client';

import type { CubeTrace } from '@/types/api';

interface APIModalProps {
  open: boolean;
  onClose: () => void;
  trace: CubeTrace | null;
}

function formatBytes(bytes: number): string {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`;
}

export default function APIModal({ open, onClose, trace }: APIModalProps) {
  if (!open) return null;

  const endpoint = trace?.endpoint ?? 'N/A';
  const method = trace?.method ?? 'N/A';
  const reqPayload = trace?.request_payload ?? {};
  const queryParams = trace?.query_parameters ?? {};
  const elapsed = trace?.execution_time_ms ?? 0;
  const status = trace?.response_status ?? 0;
  const size = trace?.response_size_bytes ?? 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Cube API request trace"
    >
      <div
        className="w-full max-w-3xl max-h-[85vh] overflow-hidden rounded-xl bg-white shadow-2xl flex flex-col"
        onClick={(evt) => evt.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">View API — Cube.dev Request</h3>
            <p className="text-sm text-gray-500 mt-0.5">
              How MetricMind translated your question into the Cube Semantic API
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-800"
            aria-label="Close API modal"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="overflow-y-auto px-6 py-5 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Endpoint</span>
              <div className="mt-1 rounded-md bg-gray-50 border border-gray-200 px-3 py-2 font-mono text-xs text-gray-800 break-all">
                {endpoint}
              </div>
            </div>
            <div>
              <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Method</span>
              <div className="mt-1 inline-flex items-center rounded-md bg-blue-50 border border-blue-200 px-3 py-1 text-xs font-semibold text-blue-700">
                {method}
              </div>
            </div>
            <div>
              <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Execution time</span>
              <div className="mt-1 text-sm text-gray-800 font-medium">
                {elapsed ? `${Number(elapsed).toFixed(1)} ms` : '—'}
              </div>
            </div>
            <div>
              <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Response status</span>
              <div
                className={`mt-1 inline-flex items-center rounded-md px-3 py-1 text-xs font-semibold ${
                  status >= 200 && status < 300
                    ? 'bg-green-50 border border-green-200 text-green-700'
                    : 'bg-red-50 border border-red-200 text-red-700'
                }`}
              >
                {status ? `${status}` : 'Pending'}
              </div>
              {size ? (
                <div className="mt-1 text-xs text-gray-500">Size: {formatBytes(size)}</div>
              ) : null}
            </div>
          </div>

          <div>
            <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Query parameters</span>
            <pre className="mt-1 rounded-md bg-gray-50 border border-gray-200 p-3 font-mono text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap">
{JSON.stringify(queryParams, null, 2)}
            </pre>
          </div>

          <div>
            <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Request payload</span>
            <pre className="mt-1 rounded-md bg-gray-50 border border-gray-200 p-3 font-mono text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap">
{JSON.stringify(reqPayload, null, 2)}
            </pre>
            <p className="mt-2 text-[11px] text-gray-500">
              Tokens, secrets and credentials are redacted by the backend before rendering here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
