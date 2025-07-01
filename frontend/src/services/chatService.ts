import api from './api';
import { ChatMessage, ChatResponse, ConversationSummary, WebSocketMessage } from '@/types/api';

export const chatService = {
  // Send chat message (REST endpoint)
  sendMessage: async (message: ChatMessage): Promise<ChatResponse> => {
    const response = await api.post('/api/v1/chat/chat', message);
    return response.data;
  },

  // Get conversation history
  getConversation: async (conversationId: string): Promise<any> => {
    const response = await api.get(`/api/v1/chat/conversations/${conversationId}`);
    return response.data;
  },

  // Delete conversation
  deleteConversation: async (conversationId: string): Promise<void> => {
    await api.delete(`/api/v1/chat/conversations/${conversationId}`);
  },

  // List conversations
  listConversations: async (userId?: string, limit = 20): Promise<ConversationSummary[]> => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    params.append('limit', limit.toString());
    
    const response = await api.get(`/api/v1/chat/conversations?${params.toString()}`);
    return response.data;
  },

  // Send feedback
  sendFeedback: async (conversationId: string, messageId: string, feedback: string, comment?: string): Promise<void> => {
    await api.post('/api/v1/chat/chat/feedback', {
      conversation_id: conversationId,
      message_id: messageId,
      feedback,
      comment,
    });
  },

  // Get chat statistics
  getChatStats: async (): Promise<any> => {
    const response = await api.get('/api/v1/chat/stats');
    return response.data;
  },

  // Classify query for caching
  classifyQuery: async (query: string): Promise<any> => {
    const response = await api.get(`/api/v1/chat/rate-limit/classify?query=${encodeURIComponent(query)}`);
    return response.data;
  },
};

// WebSocket chat service
export class ChatWebSocketService {
  private ws: WebSocket | null = null;
  private connectionId: string;
  private baseUrl: string;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();

  constructor(connectionId: string, baseUrl?: string) {
    this.connectionId = connectionId;
    this.baseUrl = baseUrl || (import.meta.env.VITE_WS_URL || 'ws://localhost:8000');
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${this.baseUrl}/api/v1/chat/ws/chat/${this.connectionId}`);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          resolve();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.ws = null;
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendMessage(message: string, conversationId?: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    this.ws.send(JSON.stringify({
      message,
      conversation_id: conversationId,
    }));
  }

  onMessage(type: string, handler: (message: WebSocketMessage) => void): void {
    this.messageHandlers.set(type, handler);
  }

  offMessage(type: string): void {
    this.messageHandlers.delete(type);
  }

  private handleMessage(message: WebSocketMessage): void {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message);
    }

    // Also call generic message handler if exists
    const genericHandler = this.messageHandlers.get('*');
    if (genericHandler) {
      genericHandler(message);
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
} 