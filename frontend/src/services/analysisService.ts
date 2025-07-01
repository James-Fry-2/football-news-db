import api from './api';
import { AnalysisResponse } from '@/types/api';

export const analysisService = {
  // Get analysis statistics
  getStats: async (): Promise<AnalysisResponse> => {
    const response = await api.get('/api/v1/analysis/stats');
    return response.data;
  },
}; 