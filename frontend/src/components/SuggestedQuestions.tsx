'use client';

interface SuggestedQuestionsProps {
  onQuestionClick: (question: string) => void;
}

const suggestedQuestions = [
  'What was the total revenue last month?',
  'Show profit by product category',
  'Which region had the highest sales?',
  'What are the top 10 customers?',
];

export default function SuggestedQuestions({
  onQuestionClick,
}: SuggestedQuestionsProps) {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Ask MetricMind AI
        </h2>
        <p className="text-gray-600">
          Get insights from your data with natural language
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {suggestedQuestions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
            className="p-4 text-left border border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all"
          >
            <p className="text-gray-700">{question}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
