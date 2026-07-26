import axios from 'axios';
import type {
  MetricsResponse,
  SalesListResponse,
  BIAnswerResponse,
  SemanticSearchResponse,
  GovernanceValidationRequest,
  GovernanceValidationResponse,
  ExplainResponse,
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const api = {
  getHealth: async () => apiClient.get('/'),

  getMetrics: async <F extends Record<string, string | undefined>>(
    filters?: F
  ): Promise<MetricsResponse> => {
    const response = await apiClient.get('/api/v1/metrics', {
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
};

