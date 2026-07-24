'use client';

import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import type { ChatMessage, Conversation } from '@/types/chat';
import { api } from '@/lib/api';

const STORAGE_KEY = 'metricmind-chat-conversations';

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
      messages: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: string }>;
      createdAt: string;
      updatedAt: string;
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

export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>(() =>
    typeof window === 'undefined'
      ? []
      : hydrateConversations(window.localStorage.getItem(STORAGE_KEY))
  );
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    const stored = hydrateConversations(window.localStorage.getItem(STORAGE_KEY));
    return stored[0]?.id ?? null;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [streamingContent, setStreamingContent] = useState('');

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  }, [conversations]);

  const messages = useMemo(
    () =>
      conversations.find((conversation) => conversation.id === currentConversationId)?.messages ?? [],
    [conversations, currentConversationId]
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const startNewConversation = useCallback(() => {
    setCurrentConversationId(null);
    setStreamingContent('');
    setError(null);
  }, []);

  const selectConversation = useCallback((conversationId: string) => {
    setCurrentConversationId(conversationId);
    setStreamingContent('');
    setError(null);
  }, []);

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

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);

    const userMessage: ChatMessage = {
      id: `${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };
    const conversationId = currentConversationId ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setCurrentConversationId(conversationId);
    upsertConversation(conversationId, (conversation) => ({
      ...conversation,
      title: conversation.messages.length === 0 ? getConversationTitle(content) : conversation.title,
      messages: [...conversation.messages, userMessage],
      updatedAt: new Date(),
    }));
    setIsLoading(true);
    setStreamingContent('');

    try {
      const response = await api.askBI(content.trim());
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
          };
          upsertConversation(conversationId, (conversation) => ({
            ...conversation,
            messages: [...conversation.messages, assistantMessage],
            updatedAt: new Date(),
          }));
          setStreamingContent('');
          setIsLoading(false);
        }
      }, 30);
    } catch (err) {
      console.error('Chat error:', err);
      setError(
        err instanceof Error ? err.message : 'An unexpected error occurred'
      );
      setIsLoading(false);
    }
  }, [currentConversationId, isLoading, upsertConversation]);

  const clearChat = useCallback(() => {
    if (!currentConversationId) {
      setError(null);
      setStreamingContent('');
      return;
    }
    setConversations((previous) =>
      previous.filter((conversation) => conversation.id !== currentConversationId)
    );
    setCurrentConversationId(null);
    setError(null);
    setStreamingContent('');
  }, [currentConversationId]);

  const clearAllChats = useCallback(() => {
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
