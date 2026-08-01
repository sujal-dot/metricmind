import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';
import type {
  MetricsResponse,
  SalesListResponse,
  BIAnswerResponse,
  SemanticSearchResponse,
} from '@/types/api';
import type { AnalyticsCharts, AnalyticsFilters } from '@/types/analytics';

export function useMetrics<F extends Record<string, string | undefined>>(filters?: F) {
  return useQuery<MetricsResponse, Error>({
    queryKey: ['metrics', filters],
    queryFn: () => api.getMetrics(filters),
    refetchOnWindowFocus: false,
    staleTime: 60000,
  });
}

export function useAnalyticsCharts(filters?: AnalyticsFilters) {
  return useQuery<AnalyticsCharts, Error>({
    queryKey: ['analyticsCharts', filters],
    queryFn: () => api.getAnalyticsCharts(filters),
    refetchOnWindowFocus: false,
    staleTime: 60000,
  });
}

export function useSales(limit = 100, offset = 0) {
  return useQuery<SalesListResponse, Error>({
    queryKey: ['sales', limit, offset],
    queryFn: () => api.getSales(limit, offset),
    refetchOnWindowFocus: false,
  });
}

export function useAskBIMutation() {
  const queryClient = useQueryClient();

  return useMutation<BIAnswerResponse, Error, string>({
    mutationFn: (question) => api.askBI(question),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatHistory'] });
    },
  });
}

export function useSemanticSearchMutation() {
  return useMutation<SemanticSearchResponse, Error, string>({
    mutationFn: (question) => api.semanticSearch(question),
  });
}
