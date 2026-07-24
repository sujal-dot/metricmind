'use client';

interface EmptyStateProps {
  onQuestionClick: (question: string) => void;
}

const suggestedQuestions = [
  'What was the total revenue last month?',
  'Show profit by product category.',
  'Which region generated the highest sales?',
  'Compare this month with last month.',
];

export default function EmptyState({ onQuestionClick }: EmptyStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-sm">
        <svg
          className="h-7 w-7"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.8}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4v-4z"
          />
        </svg>
      </div>
      <h1 className="mb-2 text-3xl font-semibold text-gray-900">How can I help with your data?</h1>
      <p className="mb-8 max-w-2xl text-sm text-gray-600">
        Ask a business question in plain language and MetricMind will query the backend BI agent.
        The UI is ready for real streaming responses and currently simulates token-by-token output
        for a smooth chat experience.
      </p>
      <div className="grid w-full max-w-3xl grid-cols-1 gap-3 md:grid-cols-2">
        {suggestedQuestions.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => onQuestionClick(question)}
            className="rounded-2xl border border-gray-200 bg-white p-4 text-left text-sm text-gray-700 transition hover:border-blue-300 hover:bg-blue-50"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
