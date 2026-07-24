'use client';

import ChatBox from '@/components/ChatBox';

export default function ChatPage() {
  return (
    <div className="h-full">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">AI Chat</h1>
      <div className="h-[calc(100vh-12rem)]">
        <ChatBox />
      </div>
    </div>
  );
}
