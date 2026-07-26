'use client';

interface SecurityBannerProps {
  message?: string;
  className?: string;
}

export default function SecurityBanner({
  message,
  className,
}: SecurityBannerProps) {
  return (
    <div
      role="note"
      className={`flex items-start gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 ${
        className ?? ''
      }`}
    >
      <svg
        className="w-5 h-5 mt-0.5 shrink-0 text-emerald-600"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden="true"
      >
        <path strokeLinecap="round" strokeLinejoin="round"
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
      <div className="flex-1 min-w-0">
        <p className="font-semibold">
          Cube.dev Only — No Direct SQL, Ever.
        </p>
        <p className="text-emerald-700 mt-0.5">
          {message ??
            'Every query passes through the governance layer, is routed exclusively via the Cube.dev Semantic API, and the raw payload & response are fully visible below.'}
        </p>
      </div>
    </div>
  );
}
