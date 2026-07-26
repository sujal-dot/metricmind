import type { CubeTrace, JsonObject, SecurityDecision } from '@/types/api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  /**
   * For assistant messages, the user question that triggered this reply.
   * Used by the intelligent visualization engine to route intent → chart type.
   */
  relatedQuestion?: string;
  /** Transparency data (Day 16) rendered as View API button. */
  cube_trace?: CubeTrace | null;
  /** Transparency data rendered as View JSON button. */
  cube_json?: JsonObject | null;
  /** Policy violation info — when the request was blocked before the API call. */
  policy_violation?: SecurityDecision | null;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}
