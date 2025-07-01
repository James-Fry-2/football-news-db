import { useQuery, useMutation, useQueryClient } from 'react-query';
import { articlesService } from '@/services';
import { Article, ArticleCreate, ArticleUpdate, ArticleFilters } from '@/types/api';
import toast from 'react-hot-toast';

// Query keys
export const articleKeys = {
  all: ['articles'] as const,
  lists: () => [...articleKeys.all, 'list'] as const,
  list: (filters?: ArticleFilters) => [...articleKeys.lists(), filters] as const,
  details: () => [...articleKeys.all, 'detail'] as const,
  detail: (url: string) => [...articleKeys.details(), url] as const,
};

// Get articles hook
export const useArticles = (filters?: ArticleFilters) => {
  return useQuery({
    queryKey: articleKeys.list(filters),
    queryFn: () => articlesService.getArticles(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Get single article hook
export const useArticle = (url: string, enabled = true) => {
  return useQuery({
    queryKey: articleKeys.detail(url),
    queryFn: () => articlesService.getArticle(url),
    enabled: enabled && !!url,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Create article mutation
export const useCreateArticle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (article: ArticleCreate) => articlesService.createArticle(article),
    onSuccess: (_newArticle: Article) => {
      // Invalidate and refetch articles list
      queryClient.invalidateQueries(articleKeys.lists());
      toast.success('Article created successfully!');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create article');
    },
  });
};

// Update article mutation
export const useUpdateArticle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ url, article }: { url: string; article: ArticleUpdate }) =>
      articlesService.updateArticle(url, article),
    onSuccess: (updatedArticle: Article) => {
      // Update specific article in cache
      queryClient.setQueryData(articleKeys.detail(updatedArticle.url), updatedArticle);
      // Invalidate articles list to ensure consistency
      queryClient.invalidateQueries(articleKeys.lists());
      toast.success('Article updated successfully!');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update article');
    },
  });
};

// Delete article mutation
export const useDeleteArticle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (url: string) => articlesService.deleteArticle(url),
    onSuccess: (_data, url) => {
      // Remove article from cache
      queryClient.removeQueries(articleKeys.detail(url));
      // Invalidate articles list
      queryClient.invalidateQueries(articleKeys.lists());
      toast.success('Article deleted successfully!');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete article');
    },
  });
}; 