import api from './api';
import { Article, ArticleCreate, ArticleUpdate, ArticleFilters } from '@/types/api';

export const articlesService = {
  // Get all articles with optional filters
  getArticles: async (filters?: ArticleFilters): Promise<Article[]> => {
    const params = new URLSearchParams();
    
    if (filters?.skip) params.append('skip', filters.skip.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.source) params.append('source', filters.source);
    if (filters?.team) params.append('team', filters.team);
    if (filters?.player) params.append('player', filters.player);
    
    const response = await api.get(`/api/v1/articles?${params.toString()}`);
    return response.data;
  },

  // Get a specific article by URL
  getArticle: async (url: string): Promise<Article> => {
    const response = await api.get(`/api/v1/articles/${encodeURIComponent(url)}`);
    return response.data;
  },

  // Create a new article
  createArticle: async (article: ArticleCreate): Promise<Article> => {
    const response = await api.post('/api/v1/articles/', article);
    return response.data;
  },

  // Update an existing article
  updateArticle: async (url: string, article: ArticleUpdate): Promise<Article> => {
    const response = await api.put(`/api/v1/articles/${encodeURIComponent(url)}`, article);
    return response.data;
  },

  // Delete an article
  deleteArticle: async (url: string): Promise<void> => {
    await api.delete(`/api/v1/articles/${encodeURIComponent(url)}`);
  },
}; 