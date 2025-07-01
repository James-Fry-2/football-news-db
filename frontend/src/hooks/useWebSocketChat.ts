import { useEffect, useState, useCallback, useRef } from 'react';
import { useQuery, useQueryClient, useMutation } from 'react-query';
import { 
  WebSocketService, 
  WebSocketMessage, 
  ChatMessage, 
  ConnectionStatus,
  getWebSocketService 
} from '@/services/websocketService';

export interface ChatHookOptions {
  conversationId?: string;
  autoConnect?: boolean;
  enableRealtimeUpdates?: boolean;
}

export interface ChatState {
  messages: WebSocketMessage[];
  isConnected: boolean;
  isConnecting: boolean;
  connectionStatus: ConnectionStatus;
  error: string | null;
}

export interface UseChatReturn {
  // State
  state: ChatState;
  
  // Actions
  sendMessage: (message: string) => Promise<void>;
  connect: () => Promise<void>;
  disconnect: () => void;
  joinConversation: (conversationId: string) => void;
  leaveConversation: (conversationId: string) => void;
  clearMessages: () => void;
  
  // WebSocket service
  websocketService: WebSocketService;
  
  // Connection management
  isReady: boolean;
  connectionId: string | null;
}

export const useWebSocketChat = (options: ChatHookOptions = {}): UseChatReturn => {
  const {
    conversationId,
    autoConnect = true,
    enableRealtimeUpdates = true,
  } = options;

  const queryClient = useQueryClient();
  const wsService = useRef<WebSocketService | null>(null);
  
  // Local state
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    connecting: false,
    error: null,
    reconnectAttempts: 0,
  });

  // Initialize WebSocket service
  useEffect(() => {
    if (!wsService.current) {
      wsService.current = getWebSocketService({
        autoConnect,
        enableLogging: process.env.NODE_ENV === 'development',
      });
      
      // Set query client for cache invalidation
      wsService.current.setQueryClient(queryClient);
    }

    return () => {
      // Cleanup on unmount
      if (wsService.current) {
        wsService.current.destroy();
        wsService.current = null;
      }
    };
  }, [autoConnect, queryClient]);

  // Setup event listeners
  useEffect(() => {
    if (!wsService.current || !enableRealtimeUpdates) return;

    const ws = wsService.current;

    // Connection status listener
    const handleStatusChange = (status: ConnectionStatus) => {
      setConnectionStatus(status);
    };

    // Message listeners
    const handleChatMessage = (message: WebSocketMessage) => {
      // Skip empty messages and system messages
      if (!message.content || message.content.trim() === '' || 
          message.type === 'ping' || message.type === 'pong' || message.type === 'system') {
        return;
      }

      setMessages(prev => [...prev, message]);
      
      // Invalidate conversation queries
      if (message.conversation_id) {
        queryClient.invalidateQueries(['conversation', message.conversation_id]);
      }
    };

    const handleToken = (data: WebSocketMessage) => {
      // Handle streaming tokens (update last message)
      if (data.content && data.content.trim() !== '') {
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && (lastMessage.type === 'token' || lastMessage.type === 'chunk')) {
            // Append to existing token message
            return [
              ...prev.slice(0, -1),
              { ...lastMessage, content: (lastMessage.content || '') + data.content }
            ];
          } else {
            // New token message
            return [...prev, data];
          }
        });
      }
    };

    const handleTyping = (data: any) => {
      // Handle typing indicators
      console.log('User is typing:', data);
    };

    const handleMessageComplete = (data: WebSocketMessage) => {
      // Handle message completion
      if (data.conversation_id) {
        queryClient.invalidateQueries(['conversation', data.conversation_id]);
        queryClient.invalidateQueries(['conversations']);
      }
    };

    const handleError = (data: WebSocketMessage) => {
      console.error('Chat error:', data);
      setConnectionStatus(prev => ({
        ...prev,
        error: data.content || 'Chat error occurred',
      }));
    };

    // Register event listeners
    ws.onStatusChange(handleStatusChange);
    ws.on('chat_message', handleChatMessage);
    ws.on('token', handleToken);
    ws.on('typing', handleTyping);
    ws.on('message_complete', handleMessageComplete);
    ws.on('error', handleError);

    // Initial status
    setConnectionStatus(ws.getConnectionStatus());

    return () => {
      // Cleanup listeners
      ws.offStatusChange(handleStatusChange);
      ws.off('chat_message', handleChatMessage);
      ws.off('token', handleToken);
      ws.off('typing', handleTyping);
      ws.off('message_complete', handleMessageComplete);
      ws.off('error', handleError);
    };
  }, [enableRealtimeUpdates, queryClient]);

  // Join conversation on mount or when conversationId changes
  useEffect(() => {
    if (wsService.current && conversationId && connectionStatus.connected) {
      wsService.current.joinRoom(`conversation:${conversationId}`);
      
      return () => {
        if (wsService.current && conversationId) {
          wsService.current.leaveRoom(`conversation:${conversationId}`);
        }
      };
    }
  }, [conversationId, connectionStatus.connected]);

  // Mutation for sending messages
  const sendMessageMutation = useMutation(
    async (message: string) => {
      if (!wsService.current?.isConnected()) {
        throw new Error('WebSocket is not connected');
      }

      // Add user message to local state immediately for better UX
      const userMessage: WebSocketMessage = {
        id: `user-${Date.now()}`,
        type: 'message_received',
        content: message.trim(),
        timestamp: new Date().toISOString(),
        sender: 'user',
        conversation_id: conversationId,
      };

      // Add to local state immediately
      setMessages(prev => [...prev, userMessage]);

      const chatMessage: ChatMessage = {
        message,
        conversation_id: conversationId,
        user_id: localStorage.getItem('userId') || undefined,
      };

      wsService.current.sendChatMessage(chatMessage);
    },
    {
      onError: (error) => {
        console.error('Failed to send message:', error);
        setConnectionStatus(prev => ({
          ...prev,
          error: 'Failed to send message',
        }));
        // Remove the optimistically added message on error
        setMessages(prev => prev.slice(0, -1));
      },
      onSuccess: () => {
        // Optionally invalidate conversation queries
        if (conversationId) {
          queryClient.invalidateQueries(['conversation', conversationId]);
        }
      },
    }
  );

  // Actions
  const connect = useCallback(async () => {
    if (wsService.current) {
      await wsService.current.connect();
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsService.current) {
      wsService.current.disconnect();
    }
  }, []);

  const sendMessage = useCallback(async (message: string) => {
    await sendMessageMutation.mutateAsync(message);
  }, [sendMessageMutation]);

  const joinConversation = useCallback((convId: string) => {
    if (wsService.current?.isConnected()) {
      wsService.current.joinRoom(`conversation:${convId}`);
    }
  }, []);

  const leaveConversation = useCallback((convId: string) => {
    if (wsService.current?.isConnected()) {
      wsService.current.leaveRoom(`conversation:${convId}`);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Computed state
  const state: ChatState = {
    messages,
    isConnected: connectionStatus.connected,
    isConnecting: connectionStatus.connecting,
    connectionStatus,
    error: connectionStatus.error,
  };

  return {
    state,
    sendMessage,
    connect,
    disconnect,
    joinConversation,
    leaveConversation,
    clearMessages,
    websocketService: wsService.current!,
    isReady: wsService.current?.isConnected() || false,
    connectionId: wsService.current?.getConnectionId() || null,
  };
};

// Hook for getting conversation messages with React Query
export const useConversationMessages = (conversationId?: string) => {
  return useQuery(
    ['conversation', conversationId],
    async () => {
      if (!conversationId) return [];
      
      // Fetch conversation history from API
      const response = await fetch(`/api/v1/chat/conversations/${conversationId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch conversation');
      }
      return response.json();
    },
    {
      enabled: !!conversationId,
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 30, // 30 minutes
    }
  );
};

// Hook for getting conversation list
export const useConversations = (userId?: string) => {
  return useQuery(
    ['conversations', userId],
    async () => {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      
      const response = await fetch(`/api/v1/chat/conversations?${params.toString()}`);
      if (!response.ok) {
        throw new Error('Failed to fetch conversations');
      }
      return response.json();
    },
    {
      staleTime: 1000 * 60 * 2, // 2 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
    }
  );
}; 