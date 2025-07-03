// WebSocket message types
export interface WebSocketMessage {
  type: 'message_received' | 'typing' | 'token' | 'message_complete' | 'error' | 'chunk' | 'system' | 'ping' | 'pong' | 'final_response' | 'cache_hit' | 'cache_miss' | 'no_cache';
  content?: string;
  conversation_id?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
  sender?: 'user' | 'assistant';
  id?: string;
  message?: string; // Some server messages use 'message' instead of 'content'
  category?: string;
  ttl_hours?: number;
}

export interface ChatMessage {
  message: string;
  conversation_id?: string;
  user_id?: string;
}

export interface ConnectionStatus {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastConnected?: Date;
  reconnectAttempts: number;
}

export interface WebSocketConfig {
  url?: string;
  autoConnect?: boolean;
  reconnection?: boolean;
  reconnectionDelay?: number;
  reconnectionAttempts?: number;
  timeout?: number;
  enableLogging?: boolean;
  auth?: {
    token?: string;
    userId?: string;
  };
}

// Event listeners type
type EventListener<T = any> = (data: T) => void;

export class WebSocketService {
  private socket: WebSocket | null = null;
  private config: WebSocketConfig;
  private connectionStatus: ConnectionStatus = {
    connected: false,
    connecting: false,
    error: null,
    reconnectAttempts: 0,
  };
  
  // Event listeners
  private listeners: Map<string, Set<EventListener>> = new Map();
  private statusListeners: Set<EventListener<ConnectionStatus>> = new Set();
  
  // Connection management
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private connectionId: string | null = null;

  constructor(config: WebSocketConfig = {}) {
    this.config = {
      url: config.url || import.meta.env.VITE_API_URL || 'http://localhost:8000',
      autoConnect: config.autoConnect ?? true,
      reconnection: config.reconnection ?? true,
      reconnectionDelay: config.reconnectionDelay ?? 1000,
      reconnectionAttempts: config.reconnectionAttempts ?? 5,
      timeout: config.timeout ?? 20000,
      enableLogging: config.enableLogging ?? true,
      auth: config.auth || {},
    };

    if (this.config.autoConnect) {
      this.connect();
    }
  }

  /**
   * Set React Query client for cache invalidation (kept for compatibility)
   */
  setQueryClient(_queryClient: any): void {
    // No-op for native WebSocket implementation
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.log('Already connected');
      return;
    }

    if (this.connectionStatus.connecting) {
      this.log('Connection already in progress');
      return;
    }

    this.updateConnectionStatus({ connecting: true, error: null });

    try {
      // Generate a unique connection ID
      this.connectionId = `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      // Convert HTTP URL to WebSocket URL
      const wsUrl = this.config.url!.replace(/^https?:/, 'ws:').replace(/^http:/, 'ws:');
      const fullUrl = `${wsUrl}/api/v1/chat/ws/chat/${this.connectionId}`;

      this.log('Connecting to:', fullUrl);
      this.socket = new WebSocket(fullUrl);
      this.setupEventHandlers();

      // Wait for connection
      await new Promise<void>((resolve, reject) => {
        const connectTimeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, this.config.timeout);

        const onOpen = () => {
          clearTimeout(connectTimeout);
          this.socket!.removeEventListener('open', onOpen);
          this.socket!.removeEventListener('error', onError);
          resolve();
        };

        const onError = (_event: Event) => {
          clearTimeout(connectTimeout);
          this.socket!.removeEventListener('open', onOpen);
          this.socket!.removeEventListener('error', onError);
          reject(new Error('WebSocket connection failed'));
        };

        this.socket!.addEventListener('open', onOpen);
        this.socket!.addEventListener('error', onError);
      });

    } catch (error) {
      this.handleConnectionError(error as Error);
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.clearReconnectTimer();
    this.clearHeartbeat();

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.updateConnectionStatus({
      connected: false,
      connecting: false,
      reconnectAttempts: 0,
    });

    this.log('Disconnected');
  }

  /**
   * Send message through WebSocket
   */
  sendMessage(event: string, data: any): void {
    if (!this.isConnected()) {
      throw new Error('WebSocket is not connected');
    }

    // For native WebSocket, we send JSON directly
    this.socket!.send(JSON.stringify(data));
    this.log(`Sent message: ${event}`, data);
  }

  /**
   * Send chat message
   */
  sendChatMessage(message: ChatMessage): void {
    if (!this.isConnected()) {
      throw new Error('WebSocket is not connected');
    }

    this.socket!.send(JSON.stringify(message));
    this.log('Sent chat message:', message);
  }

  /**
   * Join a room/namespace (no-op for this implementation)
   */
  joinRoom(room: string): void {
    this.log(`Joining room: ${room} (no-op)`);
  }

  /**
   * Leave a room/namespace (no-op for this implementation)
   */
  leaveRoom(room: string): void {
    this.log(`Leaving room: ${room} (no-op)`);
  }

  /**
   * Add event listener
   */
  on<T = any>(event: string, listener: EventListener<T>): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
  }

  /**
   * Remove event listener
   */
  off(event: string, listener?: EventListener): void {
    if (!this.listeners.has(event)) return;

    const eventListeners = this.listeners.get(event)!;
    if (listener) {
      eventListeners.delete(listener);
    } else {
      eventListeners.clear();
    }
  }

  /**
   * Add connection status listener
   */
  onStatusChange(listener: EventListener<ConnectionStatus>): void {
    this.statusListeners.add(listener);
  }

  /**
   * Remove connection status listener
   */
  offStatusChange(listener: EventListener<ConnectionStatus>): void {
    this.statusListeners.delete(listener);
  }

  /**
   * Get current connection status
   */
  getConnectionStatus(): ConnectionStatus {
    return { ...this.connectionStatus };
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection ID
   */
  getConnectionId(): string | null {
    return this.connectionId;
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      this.updateConnectionStatus({
        connected: true,
        connecting: false,
        error: null,
        lastConnected: new Date(),
        reconnectAttempts: 0,
      });
      this.startHeartbeat();
      this.log('Connected with ID:', this.connectionId);
      this.emitToListeners('connect', { connectionId: this.connectionId });
    };

    this.socket.onclose = (event) => {
      this.connectionId = null;
      this.updateConnectionStatus({
        connected: false,
        connecting: false,
        error: `Disconnected: ${event.reason || 'Unknown reason'}`,
      });
      this.clearHeartbeat();
      this.log('Disconnected:', event.reason);

      if (this.config.reconnection && event.code !== 1000) {
        this.scheduleReconnect();
      }
      
      this.emitToListeners('disconnect', { reason: event.reason });
    };

    this.socket.onerror = (error) => {
      this.log('WebSocket error:', error);
      this.handleConnectionError(new Error('WebSocket error'));
    };

    this.socket.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        this.log('Error parsing message:', error);
      }
    };
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(data: WebSocketMessage): void {
    this.log('🔄 Raw incoming message:', data);
    
    // Don't filter out messages too aggressively - let the hook decide
    if (data.type === 'ping' || data.type === 'pong') {
      this.log('⏭️ Skipping ping/pong message');
      return;
    }
    
    // Always emit to listeners for debugging and processing
    this.log('📤 Emitting message to listeners');
    this.emitToListeners('message', data);
    this.emitToListeners('chat_message', data);

    // Handle different message types
    switch (data.type) {
      case 'token':
      case 'chunk':
        this.emitToListeners('token', data);
        break;
      case 'message_complete':
        this.emitToListeners('message_complete', data);
        break;
      case 'error':
        this.emitToListeners('error', data);
        break;
      case 'typing':
        this.emitToListeners('typing', data);
        break;
      case 'message_received':
        this.emitToListeners('message_received', data);
        break;
      case 'final_response':
        // This is the complete response from the server
        this.log('🏁 Final response received:', data);
        this.emitToListeners('final_response', data);
        this.emitToListeners('assistant_message', data);
        this.emitToListeners('response', data);
        break;
      case 'cache_hit':
      case 'cache_miss':
      case 'no_cache':
        // Cache-related messages - can be shown as system messages
        this.log('💾 Cache-related message:', data);
        this.emitToListeners(data.type, data);
        break;
      default:
        // For any unknown type, also emit as a generic message
        this.log('🔍 Unknown message type, emitting as generic:', data.type);
        this.emitToListeners('assistant_message', data);
        this.emitToListeners('response', data);
        break;
    }
  }

  /**
   * Handle connection errors
   */
  private handleConnectionError(error: Error): void {
    this.log('Connection error:', error);
    this.updateConnectionStatus({
      connected: false,
      connecting: false,
      error: error.message,
    });

    if (this.config.reconnection) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.connectionStatus.reconnectAttempts >= this.config.reconnectionAttempts!) {
      this.log('Max reconnection attempts reached');
      return;
    }

    this.clearReconnectTimer();

    const delay = this.config.reconnectionDelay! * Math.pow(2, this.connectionStatus.reconnectAttempts);
    this.log(`Scheduling reconnect in ${delay}ms (attempt ${this.connectionStatus.reconnectAttempts + 1})`);

    this.reconnectTimer = setTimeout(() => {
      this.connectionStatus.reconnectAttempts++;
      this.connect().catch((error) => {
        this.log('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Clear reconnection timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Start heartbeat (ping every 30 seconds)
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        // Send a ping message (this won't be processed as a chat message)
        this.socket!.send(JSON.stringify({ type: 'ping', content: 'ping' }));
      }
    }, 30000);
  }

  /**
   * Clear heartbeat
   */
  private clearHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Update connection status and notify listeners
   */
  private updateConnectionStatus(updates: Partial<ConnectionStatus>): void {
    this.connectionStatus = { ...this.connectionStatus, ...updates };
    this.statusListeners.forEach((listener) => {
      listener(this.connectionStatus);
    });
  }

  /**
   * Emit event to listeners
   */
  private emitToListeners(event: string, data: any): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach((listener) => {
        try {
          listener(data);
        } catch (error) {
          this.log('Error in event listener:', error);
        }
      });
    }
  }

  /**
   * Log message if logging is enabled
   */
  private log(message: string, ...args: any[]): void {
    if (this.config.enableLogging) {
      console.log(`[WebSocket] ${message}`, ...args);
    }
  }

  /**
   * Cleanup method
   */
  destroy(): void {
    this.disconnect();
    this.listeners.clear();
    this.statusListeners.clear();
  }
}

// Singleton instance
let wsInstance: WebSocketService | null = null;

/**
 * Get singleton WebSocket service instance
 */
export const getWebSocketService = (config?: WebSocketConfig): WebSocketService => {
  if (!wsInstance) {
    wsInstance = new WebSocketService(config);
  }
  return wsInstance;
};

/**
 * React Hook for WebSocket connection
 */
export const useWebSocket = (config?: WebSocketConfig) => {
  const ws = getWebSocketService(config);
  
  return {
    service: ws,
    isConnected: ws.isConnected(),
    connectionStatus: ws.getConnectionStatus(),
    connect: () => ws.connect(),
    disconnect: () => ws.disconnect(),
    sendMessage: (event: string, data: any) => ws.sendMessage(event, data),
    sendChatMessage: (message: ChatMessage) => ws.sendChatMessage(message),
    on: <T = any>(event: string, listener: EventListener<T>) => ws.on(event, listener),
    off: (event: string, listener?: EventListener) => ws.off(event, listener),
  };
};