import api from './api';
import {
  SemanticSearchRequest,
  SearchResult,
  EnhancedSearchRequest,
  SearchResponse,
  SearchSuggestion,
  ProcessingStats,
} from '@/types/api';

export const searchService = {
  // Semantic search
  semanticSearch: async (request: SemanticSearchRequest): Promise<SearchResult[]> => {
    const response = await api.post('/api/v1/vector/semantic-search', request);
    return response.data;
  },

  // Enhanced search with advanced scoring
  enhancedSearch: async (request: EnhancedSearchRequest): Promise<SearchResponse> => {
    const response = await api.post('/api/v1/search/enhanced-search', request);
    return response.data;
  },

  // Get search suggestions
  getSearchSuggestions: async (query: string): Promise<SearchSuggestion> => {
    const response = await api.get(`/api/v1/search/search-suggestions?query=${encodeURIComponent(query)}`);
    return response.data;
  },

  // Get ranking strategies
  getRankingStrategies: async (): Promise<any> => {
    const response = await api.get('/api/v1/search/ranking-strategies');
    return response.data;
  },

  // Get vector processing stats
  getProcessingStats: async (): Promise<ProcessingStats> => {
    const response = await api.get('/api/v1/vector/processing-stats');
    return response.data;
  },

  // Reprocess article
  reprocessArticle: async (articleId: number): Promise<{ message: string; task_id: string }> => {
    const response = await api.post(`/api/v1/vector/reprocess/${articleId}`);
    return response.data;
  },
}; 