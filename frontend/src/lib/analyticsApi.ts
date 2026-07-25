import axios from 'axios';
import type { KPIMetrics, AnalyticsFilters } from '@/types/analytics';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const analyticsApi = {
  getMetrics: async (filters: AnalyticsFilters = {}): Promise<KPIMetrics> => {
    const response = await apiClient.get('/api/v1/metrics', { params: filters });
    return response.data;
  },
};
