import { useQuery, useMutation } from 'react-query';
import { searchService } from '@/services';
import {
  SemanticSearchRequest,
  EnhancedSearchRequest,
} from '@/types/api';
import { useDebounce } from 'use-debounce';

// Query keys
export const searchKeys = {
  all: ['search'] as const,
  semantic: (request: SemanticSearchRequest) => [...searchKeys.all, 'semantic', request] as const,
  enhanced: (request: EnhancedSearchRequest) => [...searchKeys.all, 'enhanced', request] as const,
  suggestions: (query: string) => [...searchKeys.all, 'suggestions', query] as const,
  stats: () => [...searchKeys.all, 'stats'] as const,
  strategies: () => [...searchKeys.all, 'strategies'] as const,
};

// Semantic search hook
export const useSemanticSearch = (request: SemanticSearchRequest, enabled = true) => {
  return useQuery({
    queryKey: searchKeys.semantic(request),
    queryFn: () => searchService.semanticSearch(request),
    enabled: enabled && !!request.query,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Enhanced search hook
export const useEnhancedSearch = (request: EnhancedSearchRequest, enabled = true) => {
  return useQuery({
    queryKey: searchKeys.enhanced(request),
    queryFn: () => searchService.enhancedSearch(request),
    enabled: enabled && !!request.query,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Search suggestions hook with debouncing
export const useSearchSuggestions = (query: string, debounceMs = 300) => {
  const [debouncedQuery] = useDebounce(query, debounceMs);
  
  return useQuery({
    queryKey: searchKeys.suggestions(debouncedQuery),
    queryFn: () => searchService.getSearchSuggestions(debouncedQuery),
    enabled: !!debouncedQuery && debouncedQuery.length > 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Processing stats hook
export const useProcessingStats = () => {
  return useQuery({
    queryKey: searchKeys.stats(),
    queryFn: () => searchService.getProcessingStats(),
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    staleTime: 15 * 1000, // 15 seconds
  });
};

// Ranking strategies hook
export const useRankingStrategies = () => {
  return useQuery({
    queryKey: searchKeys.strategies(),
    queryFn: () => searchService.getRankingStrategies(),
    staleTime: 60 * 60 * 1000, // 1 hour (strategies don't change often)
  });
};

// Reprocess article mutation
export const useReprocessArticle = () => {
  return useMutation({
    mutationFn: (articleId: number) => searchService.reprocessArticle(articleId),
    onSuccess: (data) => {
      console.log('Article reprocessing started:', data);
    },
    onError: (error: any) => {
      console.error('Failed to reprocess article:', error);
    },
  });
}; 