import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';
import type {
  MetricsResponse,
  SalesListResponse,
  BIQuestionRequest,
  BIAnswerResponse,
  SemanticSearchRequest,
  SemanticSearchResponse,
} from '@/types/api';

export function useMetrics() {
  return useQuery<MetricsResponse, Error>({
    queryKey: ['metrics'],
    queryFn: api.getMetrics,
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
