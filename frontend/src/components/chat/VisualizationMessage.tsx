'use client';

import dynamic from 'next/dynamic';

const ChartRouter = dynamic(
  () => import('@/components/visualization/ChartRouter'),
  { ssr: false }
);

interface VisualizationMessageProps {
  userQuestion: string;
  assistantAnswer: string;
  cubeResponse?: Record<string, unknown> | null;
}

export default function VisualizationMessage({
  userQuestion,
  cubeResponse,
}: VisualizationMessageProps) {
  if (!userQuestion || !userQuestion.trim()) return null;

  return (
    <div className="bg-gray-50 py-4 border-t border-b border-gray-100">
      <div className="max-w-3xl mx-auto px-4">
        <ChartRouter question={userQuestion} cubeResponse={cubeResponse ?? null} />
      </div>
    </div>
  );
}
