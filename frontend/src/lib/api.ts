import axios, { AxiosError } from 'axios';
import type {
  MetricsResponse,
  SalesListResponse,
  BIAnswerResponse,
  SemanticSearchResponse,
  GovernanceValidationRequest,
  GovernanceValidationResponse,
  ExplainResponse,
} from '@/types/api';
import type { AnalyticsCharts, AnalyticsFilters } from '@/types/analytics';
import type { Conversation, ChatMessage } from '@/types/chat';
import type { User } from '@/types/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^| )metricmind_csrf=([^;]+)'));
  if (match) return match[2];
  return null;
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers.set('X-CSRF-Token', csrfToken);
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

type ConversationListResponse = Array<{
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}>;

type ConversationWithMessagesResponse = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages: Array<{
    id: string | number;
    role: string;
    content: string;
    created_at: string;
    metadata?: Record<string, unknown>;
  }>;
};

type MessageResponse = {
  id: string | number;
  role: string;
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
};

type EnsureDevUserResponse = {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
};

export const api = {
  getHealth: async () => apiClient.get('/api/v1/health'),

  login: async (email: string, password: string): Promise<{ user: User }> => {
    const response = await apiClient.post<{ user: User }>('/api/v1/auth/login', { email, password });
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout');
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    return response.data;
  },

  getMetrics: async <F extends Record<string, string | undefined>>(
    filters?: F
  ): Promise<MetricsResponse> => {
    const response = await apiClient.get('/api/v1/metrics', {
      params: filters,
    });
    return response.data;
  },

  getAnalyticsCharts: async (
    filters?: AnalyticsFilters
  ): Promise<AnalyticsCharts> => {
    const response = await apiClient.get('/api/v1/analytics/charts', {
      params: filters,
    });
    return response.data;
  },

  getSales: async (limit = 100, offset = 0): Promise<SalesListResponse> => {
    const response = await apiClient.get('/api/v1/sales', {
      params: { limit, offset },
    });
    return response.data;
  },

  askBI: async (question: string): Promise<BIAnswerResponse> => {
    const response = await apiClient.post('/ask', { question });
    return response.data;
  },

  semanticSearch: async (question: string): Promise<SemanticSearchResponse> => {
    const response = await apiClient.post('/semantic-search', { question });
    return response.data;
  },

  governanceValidate: async (
    payload: GovernanceValidationRequest
  ): Promise<GovernanceValidationResponse> => {
    const response = await apiClient.post('/governance/validate', payload);
    return response.data;
  },

  explainQuestion: async (question: string): Promise<ExplainResponse> => {
    const response = await apiClient.post('/explain', { question });
    return response.data;
  },

  listConversations: async (): Promise<Conversation[]> => {
    const response = await apiClient.get<ConversationListResponse>('/api/v1/conversations');
    return response.data.map((item) => ({
      id: item.id,
      title: item.title,
      messages: [],
      createdAt: new Date(item.created_at),
      updatedAt: new Date(item.updated_at),
      messageCount: item.message_count,
    }));
  },

  createConversation: async (title?: string): Promise<Conversation> => {
    const payload = title && title.trim() ? { title } : {};
    const response = await apiClient.post<{
      id: string;
      title: string;
      created_at: string;
      updated_at: string;
      message_count?: number;
    }>('/api/v1/conversations', payload);
    const d = response.data;
    return {
      id: d.id,
      title: d.title,
      messages: [],
      createdAt: new Date(d.created_at),
      updatedAt: new Date(d.updated_at),
      messageCount: d.message_count ?? 0,
    };
  },

  getConversation: async (id: string): Promise<Conversation & { messages: ChatMessage[] }> => {
    const response = await apiClient.get<ConversationWithMessagesResponse>(
      `/api/v1/conversations/${encodeURIComponent(id)}`
    );
    const d = response.data;
    return {
      id: d.id,
      title: d.title,
      createdAt: new Date(d.created_at),
      updatedAt: new Date(d.updated_at),
      messageCount: d.message_count,
      messages: d.messages.map((m) => ({
        id: String(m.id),
        role: m.role as ChatMessage['role'],
        content: m.content,
        timestamp: new Date(m.created_at),
        metadata: m.metadata,
      })),
    };
  },

  updateConversation: async (id: string, title: string): Promise<void> => {
    await apiClient.put(`/api/v1/conversations/${encodeURIComponent(id)}`, { title });
  },

  deleteConversation: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/conversations/${encodeURIComponent(id)}`);
  },

  appendMessage: async (
    id: string,
    msg: { role: string; content: string; metadata?: Record<string, unknown> }
  ): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>(
      `/api/v1/conversations/${encodeURIComponent(id)}/messages`,
      msg
    );
    return response.data;
  },

};
