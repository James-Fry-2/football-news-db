import api from './api';
import { UserTierRequest, RateLimitStats } from '@/types/api';

export const adminService = {
  // Set user tier
  setUserTier: async (request: UserTierRequest): Promise<any> => {
    const response = await api.post('/api/v1/admin/set-tier', request);
    return response.data;
  },

  // Get user tier
  getUserTier: async (userId: string): Promise<any> => {
    const response = await api.get(`/api/v1/admin/tier/${userId}`);
    return response.data;
  },

  // Get rate limit stats
  getRateLimitStats: async (userId?: string): Promise<RateLimitStats> => {
    const params = userId ? `?user_id=${userId}` : '';
    const response = await api.get(`/api/v1/admin/rate-limit/stats${params}`);
    return response.data;
  },

  // Reset rate limits
  resetRateLimits: async (userId: string): Promise<any> => {
    const response = await api.post(`/api/v1/admin/rate-limit/reset/${userId}`);
    return response.data;
  },
}; 