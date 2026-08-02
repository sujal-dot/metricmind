'use client';

import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import TypingIndicator from './TypingIndicator';
import EmptyState from './EmptyState';
import SidebarHistory from './SidebarHistory';
import VisualizationMessage from './chat/VisualizationMessage';
import { SecurityBanner } from './governance';
import type { ChatMessage as ChatMessageType } from '@/types/chat';
import { useChat } from '@/hooks/useChat';

function StreamingMessage({ content }: { content: string }) {
  const message: ChatMessageType = {
    id: 'streaming',
    role: 'assistant',
    content,
    timestamp: new Date(),
  };
  return <ChatMessage message={message} />;
}

export default function ChatWindow() {
  const {
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
  } = useChat();

  return (
    <div className="flex h-[calc(100vh-6rem)] overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
      <SidebarHistory
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={selectConversation}
        onNewChat={startNewConversation}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-sm font-semibold text-white">
              AI
            </div>
            <div>
              <p className="font-semibold text-gray-900">MetricMind AI</p>
              <p className="text-xs text-gray-500">Business intelligence assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {conversations.length > 0 && (
              <button
                type="button"
                onClick={clearAllChats}
                className="rounded-lg px-3 py-2 text-sm text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
              >
                Clear all
              </button>
            )}
            {messages.length > 0 && (
              <button
                type="button"
                onClick={clearChat}
                className="rounded-lg px-3 py-2 text-sm text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
              >
                Clear chat
              </button>
            )}
          </div>
        </div>

        <div className="px-4 pt-4">
          <SecurityBanner />
        </div>

        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 && !isLoading ? (
            <EmptyState onQuestionClick={sendMessage} />
          ) : (
            <>
              {messages.map((message) => (
                <div key={message.id}>
                  <ChatMessage message={message} />
                  {message.role === 'assistant' && message.relatedQuestion && message.cube_json ? (
                    <VisualizationMessage
                      userQuestion={message.relatedQuestion}
                      assistantAnswer={message.content}
                      cubeResponse={message.cube_json as Record<string, unknown>}
                    />
                  ) : message.role === 'assistant' && message.relatedQuestion ? (
                    <VisualizationMessage
                      userQuestion={message.relatedQuestion}
                      assistantAnswer={message.content}
                    />
                  ) : null}
                </div>
              ))}
              {isLoading && (
                <>
                  {streamingContent ? <StreamingMessage content={streamingContent} /> : <TypingIndicator />}
                </>
              )}
            </>
          )}
          {error && (
            <div className="mx-auto my-4 max-w-3xl rounded-lg border border-red-200 bg-red-50 px-4 py-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <ChatInput
          onSend={sendMessage}
          disabled={isLoading}
          placeholder="Ask about revenue, profit, customers, regions, or trends..."
        />
      </div>
    </div>
  );
}
