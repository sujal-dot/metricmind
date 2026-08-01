import type { CubeTrace, JsonObject, SecurityDecision } from '@/types/api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: JsonObject;
  relatedQuestion?: string;
  cube_trace?: CubeTrace | null;
  cube_json?: JsonObject | null;
  policy_violation?: SecurityDecision | null;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  messageCount?: number;
}
