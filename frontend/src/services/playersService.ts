import api from './api';
import { Player, PlayerCreate, PlayerUpdate, PaginationParams } from '@/types/api';

export const playersService = {
  // Get all players
  getPlayers: async (params?: PaginationParams): Promise<Player[]> => {
    const queryParams = new URLSearchParams();
    
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    
    const response = await api.get(`/api/v1/players?${queryParams.toString()}`);
    return response.data;
  },

  // Get a specific player by ID
  getPlayer: async (playerId: number): Promise<Player> => {
    const response = await api.get(`/api/v1/players/${playerId}`);
    return response.data;
  },

  // Create a new player
  createPlayer: async (player: PlayerCreate): Promise<Player> => {
    const response = await api.post('/api/v1/players/', player);
    return response.data;
  },

  // Update an existing player
  updatePlayer: async (playerId: number, player: PlayerUpdate): Promise<Player> => {
    const response = await api.put(`/api/v1/players/${playerId}`, player);
    return response.data;
  },

  // Delete a player (if endpoint exists)
  deletePlayer: async (playerId: number): Promise<void> => {
    await api.delete(`/api/v1/players/${playerId}`);
  },
}; 