'use client';

import type { Conversation } from '@/types/chat';

interface SidebarHistoryProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}

export default function SidebarHistory({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewChat,
}: SidebarHistoryProps) {
  return (
    <aside className="hidden h-full w-72 flex-col border-r border-gray-200 bg-gray-50 lg:flex">
      <div className="p-4 border-b border-gray-200">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No conversations yet
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                type="button"
                onClick={() => onSelectConversation(conversation.id)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm transition ${
                  currentConversationId === conversation.id
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="truncate font-medium">{conversation.title}</div>
                <div className="mt-1 truncate text-xs text-gray-500">
                  {conversation.messages.at(-1)?.content || 'No messages yet'}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
