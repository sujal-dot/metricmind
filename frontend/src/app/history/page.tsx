'use client';

import HistoryTable from '@/components/HistoryTable';
import type { HistoryItem } from '@/types/api';

// Mock data
const mockHistory: HistoryItem[] = [
  {
    id: '1',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    userQuestion: 'What was the total revenue last month?',
    aiResponse: 'Total revenue last month was $42,000.',
    status: 'success',
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    userQuestion: 'Show profit by region',
    aiResponse: 'North America: $18,000, Europe: $12,000, Asia: $8,000, Other: $4,000.',
    status: 'success',
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    userQuestion: 'Top 10 customers',
    aiResponse: 'Here are the top 10 customers by total purchase amount...',
    status: 'success',
  },
];

export default function HistoryPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Query History</h1>
      <HistoryTable data={mockHistory} />
    </div>
  );
}
