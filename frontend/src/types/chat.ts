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
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}
