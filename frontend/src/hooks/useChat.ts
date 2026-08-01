'use client';

import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import type { ChatMessage, Conversation } from '@/types/chat';
import type { SecurityDecision, CubeTrace, JsonObject } from '@/types/api';
import { api } from '@/lib/api';
import { useAuth } from '@/providers/AuthProvider';

const STORAGE_KEY = 'metricmind-chat-conversations';
const BACKEND_FAIL_WARN =
  '[useChat] Backend conversation API unavailable. Falling back to localStorage-only mode.';

function getStorageKey(userId?: number) {
  return userId ? `${STORAGE_KEY}-${userId}` : STORAGE_KEY;
}

function getConversationTitle(content: string): string {
  const cleaned = content.trim().replace(/\s+/g, ' ');
  return cleaned.length > 48 ? `${cleaned.slice(0, 48)}...` : cleaned;
}

function hydrateConversations(raw: string | null): Conversation[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as Array<{
      id: string;
      title: string;
      messages: Array<{
        id: string;
        role: 'user' | 'assistant' | 'system';
        content: string;
        timestamp: string;
        metadata?: JsonObject;
        relatedQuestion?: string;
        cube_trace?: CubeTrace | null;
        cube_json?: JsonObject | null;
        policy_violation?: SecurityDecision | null;
      }>;
      createdAt: string;
      updatedAt: string;
      messageCount?: number;
    }>;
    return parsed.map((conversation) => ({
      ...conversation,
      messages: conversation.messages.map((message) => ({
        ...message,
        timestamp: new Date(message.timestamp),
      })),
      createdAt: new Date(conversation.createdAt),
      updatedAt: new Date(conversation.updatedAt),
    }));
  } catch {
    return [];
  }
}

const syncedConversationIdsRef = { current: new Set<string>() };
const syncingConversationIdsRef = { current: new Set<string>() };

async function fireForget(p: Promise<unknown>, label: string): Promise<void> {
  try {
    await p;
  } catch (err) {
    if (typeof console !== 'undefined') {
      console.warn(`${BACKEND_FAIL_WARN} (${label})`, err);
    }
  }
}

export function useChat() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>(() =>
    typeof window === 'undefined'
      ? []
      : hydrateConversations(window.localStorage.getItem(getStorageKey(user?.id)))
  );
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    const stored = hydrateConversations(window.localStorage.getItem(getStorageKey(user?.id)));
    return stored[0]?.id ?? null;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [streamingContent, setStreamingContent] = useState('');

  // Hydrate initial chat list from backend once per user session
  useEffect(() => {
    if (!user) return;
    api.listConversations()
      .then((list) => {
        if (list.length > 0) {
          setConversations((prev) => {
            // Keep local un-synced conversations, append backend ones
            const existingIds = new Set(prev.map(c => c.id));
            const newBackend = list.filter(c => !existingIds.has(c.id));
            return [...prev, ...newBackend].sort(
              (a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
            );
          });
          if (!currentConversationId) {
            setCurrentConversationId(list[0].id);
          }
        }
      })
      .catch((err) => {
        console.warn('Failed to hydrate backend conversations', err);
      });
  }, [user, currentConversationId]);

  useEffect(() => {
    if (typeof window !== 'undefined' && user) {
      try {
        const minimal = conversations.map(c => ({
          ...c,
          messages: c.messages.slice(-50).map(m => ({
            ...m,
            // Do not store large traces in localStorage
            cube_trace: undefined,
            cube_json: undefined
          }))
        })).slice(0, 25);
        window.localStorage.setItem(getStorageKey(user.id), JSON.stringify(minimal));
      } catch (e) {
        console.warn('Failed to save to localStorage', e);
      }
    }
  }, [conversations, user]);

  const messages = useMemo(
    () =>
      conversations.find((conversation) => conversation.id === currentConversationId)?.messages ?? [],
    [conversations, currentConversationId]
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const replaceConversationId = useCallback(
    (oldId: string, newId: string) => {
      setConversations((previous) =>
        previous.map((c) => {
          if (c.id !== oldId) return c;
          return { ...c, id: newId, updatedAt: new Date() };
        })
      );
      setCurrentConversationId((prev) => (prev === oldId ? newId : prev));
    },
    []
  );

  const upsertConversation = useCallback(
    (conversationId: string, updater: (conversation: Conversation) => Conversation) => {
      setConversations((previous) => {
        const existing = previous.find((conversation) => conversation.id === conversationId);
        const baseConversation: Conversation =
          existing ??
          {
            id: conversationId,
            title: 'New conversation',
            messages: [],
            createdAt: new Date(),
            updatedAt: new Date(),
            messageCount: 0,
          };
        const updatedConversation = updater(baseConversation);
        const remaining = previous.filter((conversation) => conversation.id !== conversationId);
        return [updatedConversation, ...remaining].sort(
          (left, right) => right.updatedAt.getTime() - left.updatedAt.getTime()
        );
      });
    },
    []
  );

  const ensureBackendConversation = useCallback(
    async (localId: string, title: string): Promise<string | null> => {
      if (syncedConversationIdsRef.current.has(localId)) return localId;
      if (syncingConversationIdsRef.current.has(localId)) return null;
      syncingConversationIdsRef.current.add(localId);
      try {
        const created = await api.createConversation(title || undefined);
        syncedConversationIdsRef.current.add(created.id);
        replaceConversationId(localId, created.id);
        return created.id;
      } catch (err) {
        if (typeof console !== 'undefined') {
          console.warn(BACKEND_FAIL_WARN + ' (createConversation)', err);
        }
        return null;
      } finally {
        syncingConversationIdsRef.current.delete(localId);
      }
    },
    [replaceConversationId]
  );

  const appendMessageToBackend = useCallback(
    async (cid: string, msg: { role: string; content: string; metadata?: JsonObject }) => {
      try {
        await api.appendMessage(cid, msg);
      } catch (err) {
        if (typeof console !== 'undefined') {
          console.warn(BACKEND_FAIL_WARN + ' (appendMessage)', err);
        }
      }
    },
    []
  );

  const startNewConversation = useCallback(() => {
    setCurrentConversationId(null);
    setStreamingContent('');
    setError(null);
  }, []);

  const selectConversation = useCallback(
    async (conversationId: string) => {
      setCurrentConversationId(conversationId);
      setStreamingContent('');
      setError(null);
      fireForget(
        (async () => {
          try {
            const fromBackend = await api.getConversation(conversationId);
            syncedConversationIdsRef.current.add(conversationId);
            setConversations((previous) => {
              const remaining = previous.filter((c) => c.id !== conversationId);
              const merged: Conversation = {
                id: fromBackend.id,
                title: fromBackend.title || 'Conversation',
                createdAt: fromBackend.createdAt,
                updatedAt: fromBackend.updatedAt,
                messageCount: fromBackend.messageCount,
                messages: fromBackend.messages.map((m) => {
                  const existing = previous
                    .find((c) => c.id === conversationId)
                    ?.messages.find((em) => String(em.id) === String(m.id));
                  return {
                    ...m,
                    relatedQuestion: existing?.relatedQuestion,
                    cube_trace: existing?.cube_trace ?? m.metadata?.cube_trace ?? undefined,
                    cube_json: existing?.cube_json ?? m.metadata?.cube_json ?? undefined,
                    policy_violation: existing?.policy_violation,
                  };
                }),
              };
              return [merged, ...remaining].sort(
                (a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
              );
            });
          } catch (err) {
            if (typeof console !== 'undefined') {
              console.warn(BACKEND_FAIL_WARN + ' (getConversation on select)', err);
            }
          }
        })(),
        'hydrate-conversation'
      );
    },
    []
  );

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setError(null);

      const question = content.trim();
      const userMessage: ChatMessage = {
        id: `${Date.now()}`,
        role: 'user',
        content: question,
        timestamp: new Date(),
      };
      const localConversationId =
        currentConversationId ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const firstMessage =
        !conversations.find((c) => c.id === localConversationId)?.messages.length;

      setCurrentConversationId(localConversationId);
      upsertConversation(localConversationId, (conversation) => ({
        ...conversation,
        title: firstMessage ? getConversationTitle(content) : conversation.title,
        messages: [...conversation.messages, userMessage],
        updatedAt: new Date(),
      }));

      setIsLoading(true);
      setStreamingContent('');

      let finalConversationId = localConversationId;

      try {
        // Ensure backend conversation exists before validating/sending
        if (!syncedConversationIdsRef.current.has(localConversationId)) {
          const createdId = await ensureBackendConversation(
            localConversationId,
            firstMessage ? getConversationTitle(content) : 'Conversation'
          );
          if (createdId) {
            finalConversationId = createdId;
          }
        }

        await appendMessageToBackend(finalConversationId, {
          role: userMessage.role,
          content: userMessage.content,
        });

        let decision: SecurityDecision | null = null;
        try {
          const validation = await api.governanceValidate({ question, route: '/ask' });
          decision = validation.decision;
        } catch (err) {
          throw new Error('Unable to validate this request with governance. Please retry.');
        }

        if (decision && !decision.allowed) {
          const blockedMessage: ChatMessage = {
            id: `${Date.now() + 1}`,
            role: 'assistant',
            content:
              'This request was blocked by the MetricMind governance policy before being sent to the analytics engine. See the details below.',
            timestamp: new Date(),
            relatedQuestion: question,
            policy_violation: decision,
          };
          upsertConversation(finalConversationId, (conversation) => ({
            ...conversation,
            messages: [...conversation.messages, blockedMessage],
            updatedAt: new Date(),
          }));
          fireForget(
            appendMessageToBackend(finalConversationId, {
              role: blockedMessage.role,
              content: blockedMessage.content,
              metadata: {
                relatedQuestion: blockedMessage.relatedQuestion,
                policy_violation: (blockedMessage.policy_violation as unknown) as JsonObject,
              },
            }),
            'sync-blocked-assistant-message'
          );
          setIsLoading(false);
          setError(decision.block_reason ?? 'Request blocked by the governance policy.');
          return;
        }

        const response = await api.askBI(question);
        const fullContent = response.answer;
        if (!fullContent.trim()) {
          throw new Error('The assistant returned an empty response.');
        }
        let index = 0;
        const chunkSize = Math.max(1, Math.floor(fullContent.length / 50));

        const streamInterval = setInterval(() => {
          if (index < fullContent.length) {
            index += chunkSize;
            if (index > fullContent.length) index = fullContent.length;
            setStreamingContent(fullContent.slice(0, index));
          } else {
            clearInterval(streamInterval);
            const assistantMessage: ChatMessage = {
              id: `${Date.now() + 1}`,
              role: 'assistant',
              content: fullContent,
              timestamp: new Date(),
              relatedQuestion: question,
              cube_trace: response.cube_trace ?? null,
              cube_json: response.cube_json ?? null,
            };
            upsertConversation(finalConversationId, (conversation) => ({
              ...conversation,
              messages: [...conversation.messages, assistantMessage],
              updatedAt: new Date(),
            }));
            fireForget(
              (async () => {
                const metadata: JsonObject = {};
                if (assistantMessage.relatedQuestion) {
                  metadata.relatedQuestion = assistantMessage.relatedQuestion;
                }
                if (assistantMessage.cube_trace) {
                  metadata.cube_trace = assistantMessage.cube_trace as unknown as JsonObject;
                }
                if (assistantMessage.cube_json) {
                  metadata.cube_json = assistantMessage.cube_json;
                }
                await appendMessageToBackend(finalConversationId, {
                  role: assistantMessage.role,
                  content: assistantMessage.content,
                  metadata,
                });
              })(),
              'sync-assistant-message'
            );
            setStreamingContent('');
            setIsLoading(false);
          }
        }, 30);
      } catch (err) {
        console.error('Chat error:', err);
        setError(err instanceof Error ? err.message : 'An unexpected error occurred');
        setIsLoading(false);
      }
    },
    [
      currentConversationId,
      isLoading,
      upsertConversation,
      conversations,
      ensureBackendConversation,
      appendMessageToBackend,
    ]
  );

  const clearChat = useCallback(() => {
    if (!currentConversationId) {
      setError(null);
      setStreamingContent('');
      return;
    }
    const cid = currentConversationId;
    fireForget(
      (async () => {
        try {
          await api.deleteConversation(cid);
        } catch (err) {
          if (typeof console !== 'undefined') {
            console.warn(BACKEND_FAIL_WARN + ' (deleteConversation)', err);
          }
        }
      })(),
      'delete-conversation'
    );
    syncedConversationIdsRef.current.delete(cid);
    setConversations((previous) =>
      previous.filter((conversation) => conversation.id !== currentConversationId)
    );
    setCurrentConversationId(null);
    setError(null);
    setStreamingContent('');
  }, [currentConversationId]);

  const clearAllChats = useCallback(() => {
    fireForget(
      (async () => {
        try {
          const list = await api.listConversations();
          await Promise.all(list.map((c) => api.deleteConversation(c.id).catch(() => undefined)));
        } catch (err) {
          if (typeof console !== 'undefined') {
            console.warn(BACKEND_FAIL_WARN + ' (deleteAllConversations)', err);
          }
        }
      })(),
      'clear-all-conversations'
    );
    syncedConversationIdsRef.current.clear();
    setConversations([]);
    setCurrentConversationId(null);
    setError(null);
    setStreamingContent('');
  }, []);

  return {
    conversations,
    currentConversationId,
    messages,
    streamingContent,
    isLoading,
    error,
    messagesEndRef,
    sendMessage,
    clearChat,
    clearAllChats,
    selectConversation,
    startNewConversation,
  };
}
