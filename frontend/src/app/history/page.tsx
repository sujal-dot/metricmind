'use client';

import { useEffect, useState } from 'react';
import HistoryTable from '@/components/HistoryTable';
import type { HistoryItem } from '@/types/api';
import type { Conversation, ChatMessage } from '@/types/chat';
import { api } from '@/lib/api';
import { useChat } from '@/hooks/useChat';

function conversationsToHistoryItems(
  conversations: Array<Conversation & { messages?: ChatMessage[] }>
): HistoryItem[] {
  const items: HistoryItem[] = [];
  for (const conv of conversations) {
    const msgs = conv.messages ?? [];
    for (let i = 0; i < msgs.length; i++) {
      const m = msgs[i];
      if (m.role === 'user') {
        let assistantMsg: ChatMessage | undefined;
        for (let j = i + 1; j < msgs.length; j++) {
          if (msgs[j].role === 'assistant') {
            assistantMsg = msgs[j];
            break;
          }
        }
        if (!assistantMsg) {
          continue;
        }
        items.push({
          id: `${conv.id}-${m.id}`,
          timestamp: assistantMsg.timestamp instanceof Date
            ? assistantMsg.timestamp.toISOString()
            : String(assistantMsg.timestamp),
          userQuestion: m.content,
          aiResponse: assistantMsg.content,
          status: assistantMsg.policy_violation && !assistantMsg.policy_violation.allowed
            ? 'error'
            : 'success',
        });
      }
    }
  }
  items.sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1));
  return items;
}

function HistoryTableSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Question
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Response
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {[0, 1, 2].map((i) => (
              <tr key={i}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
                </td>
                <td className="px-6 py-4">
                  <div className="h-4 w-64 bg-gray-200 rounded animate-pulse" />
                </td>
                <td className="px-6 py-4">
                  <div className="h-4 w-80 bg-gray-200 rounded animate-pulse" />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="h-5 w-16 bg-gray-200 rounded-full animate-pulse" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function HistoryPage() {
  const { conversations: localStorageConversations } = useChat();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingFallback, setUsingFallback] = useState(false);
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        setUsingFallback(false);

        const convs = await api.listConversations();

        // Use a parallel limit to avoid N+1 slow sequential fetches, but batch them.
        const hydrated: Array<Conversation & { messages: ChatMessage[] }> = [];
        const BATCH_SIZE = 5;
        for (let i = 0; i < convs.length; i += BATCH_SIZE) {
          const batch = convs.slice(i, i + BATCH_SIZE);
          const results = await Promise.all(
            batch.map(async (c) => {
              try {
                return await api.getConversation(c.id);
              } catch (hydErr) {
                console.warn(`[history] Failed to hydrate conversation ${c.id}`, hydErr);
                return null;
              }
            })
          );
          for (const res of results) {
            if (res) hydrated.push(res);
          }
        }

        if (cancelled) return;
        setHistoryItems(conversationsToHistoryItems(hydrated));
      } catch (err) {
        if (cancelled) return;
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
        setUsingFallback(true);
        setHistoryItems(conversationsToHistoryItems(localStorageConversations));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Query History</h1>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
        >
          <div className="flex items-start gap-2">
            <span className="font-semibold">Failed to load conversations.</span>
            <span className="text-red-700">Showing local history as fallback.</span>
          </div>
          {usingFallback && (
            <div className="mt-1 text-xs text-red-600">
            Error: {error}
          </div>
          )}
        </div>
      )}

      {loading ? (
        <HistoryTableSkeleton />
      ) : historyItems.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 px-6 py-16 text-center">
          <h3 className="text-base font-semibold text-gray-700">No conversations yet</h3>
          <p className="mt-2 text-sm text-gray-500">
            Ask a question in the chat to start building your query history.
          </p>
        </div>
      ) : (
        <HistoryTable data={historyItems} />
      )}
    </div>
  );
}
