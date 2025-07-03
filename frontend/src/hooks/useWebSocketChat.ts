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
      console.log('📨 Received WebSocket message:', message);
      
      // Extract content from either 'content' or 'message' field
      const messageContent = message.content || message.message || '';
      
      // More permissive filtering - only skip truly empty or system messages
      if (!message || 
          !messageContent || 
          messageContent.trim() === '' ||
          message.type === 'ping' || 
          message.type === 'pong') {
        console.log('⏭️ Skipping message due to content/type filter:', message);
        return;
      }

      // Create a better message ID that includes content hash to prevent duplicates
      const contentHash = btoa(messageContent.substring(0, 50)).replace(/[+/=]/g, '');
      const messageId = message.id || `${message.type}-${Date.now()}-${contentHash}`;

      // Generate processed message
      const processedMessage = {
        ...message,
        id: messageId,
        timestamp: message.timestamp || new Date().toISOString(),
        sender: message.sender || 'assistant', // Default to assistant for server messages
        content: messageContent, // Ensure we always use the correct content
      };

      console.log('✅ Adding processed message to state:', processedMessage);
      
      setMessages(prev => {
        // Prevent duplicate messages - check for both ID and content similarity
        const existingMessage = prev.find(m => 
          m.id === processedMessage.id || 
          (m.content === processedMessage.content && m.sender === processedMessage.sender)
        );
        
        if (existingMessage) {
          console.log('🔄 Duplicate message detected, skipping:', processedMessage.id);
          return prev;
        }
        
        const newMessages = [...prev, processedMessage];
        console.log('📋 Updated messages array length:', newMessages.length);
        return newMessages;
      });
      
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

    const cacheHitListener = (data: any) => console.log('💾 Cache hit:', data);
    const cacheMissListener = (data: any) => console.log('💾 Cache miss:', data);
    const noCacheListener = (data: any) => console.log('💾 No cache:', data);
    
    // Register event listeners - prioritize final_response to avoid duplicates
    ws.onStatusChange(handleStatusChange);
    ws.on('final_response', handleChatMessage); // Primary listener for complete server responses
    // ws.on('chat_message', handleChatMessage); // Commenting out to prevent duplicates
    ws.on('cache_hit', cacheHitListener);
    ws.on('cache_miss', cacheMissListener);
    ws.on('no_cache', noCacheListener);
    ws.on('token', handleToken);
    ws.on('typing', handleTyping);
    ws.on('message_complete', handleMessageComplete);
    ws.on('error', handleError);

    // Add a generic listener to catch all events for debugging
    if (process.env.NODE_ENV === 'development') {
      const debugListener = (data: any) => {
        console.log('🎯 WebSocket event received:', data);
      };
      ws.on('*', debugListener);
    }

    // Initial status
    setConnectionStatus(ws.getConnectionStatus());

    return () => {
      // Cleanup listeners
      ws.offStatusChange(handleStatusChange);
      ws.off('final_response', handleChatMessage);
      // ws.off('chat_message', handleChatMessage); // Corresponding cleanup for commented listener
      ws.off('cache_hit', cacheHitListener);
      ws.off('cache_miss', cacheMissListener);
      ws.off('no_cache', noCacheListener);
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
      
      const { chatService } = await import('../services/chatService');
      return await chatService.getConversation(conversationId);
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
      const { chatService } = await import('../services/chatService');
      return await chatService.listConversations(userId);
    },
    {
      staleTime: 1000 * 60 * 2, // 2 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
    }
  );
}; 