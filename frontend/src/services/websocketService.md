# WebSocket Service Documentation

A comprehensive WebSocket service class for connecting to FastAPI backend using Socket.io client with TypeScript support, connection management, and React Query integration.

## Features

- **Socket.io Client Integration**: Full Socket.io client support with TypeScript
- **Connection Management**: Automatic connection, reconnection with exponential backoff
- **Error Handling**: Comprehensive error handling with user notifications
- **React Query Integration**: Automatic cache invalidation on WebSocket events
- **TypeScript Support**: Full type safety for all WebSocket messages and events
- **Singleton Pattern**: Single WebSocket connection shared across the application
- **Event System**: Flexible event listener system for handling various message types
- **Heartbeat/Ping**: Automatic connection health monitoring
- **Room Management**: Join/leave rooms for targeted messaging

## Quick Start

```typescript
import { useWebSocketChat } from '@/hooks/useWebSocketChat';

function ChatComponent() {
  const { state, sendMessage, isReady } = useWebSocketChat({
    conversationId: 'conv-123',
    autoConnect: true,
  });

  return (
    <div>
      <div>Status: {state.isConnected ? 'Connected' : 'Disconnected'}</div>
      <button 
        onClick={() => sendMessage('Hello!')} 
        disabled={!isReady}
      >
        Send Message
      </button>
    </div>
  );
}
```

## Configuration

```typescript
interface WebSocketConfig {
  url?: string;                    // WebSocket server URL
  autoConnect?: boolean;           // Auto-connect on initialization
  reconnection?: boolean;          // Enable automatic reconnection
  reconnectionDelay?: number;      // Initial reconnection delay (ms)
  reconnectionAttempts?: number;   // Max reconnection attempts
  timeout?: number;                // Connection timeout (ms)
  enableLogging?: boolean;         // Enable console logging
  auth?: {                         // Authentication
    token?: string;
    userId?: string;
  };
}
```

## Integration with React Query

The service automatically invalidates React Query cache when WebSocket events occur:

```typescript
import { useConversationMessages } from '@/hooks/useWebSocketChat';

function ConversationView({ conversationId }: { conversationId: string }) {
  const { data: messages, isLoading } = useConversationMessages(conversationId);
  // Messages automatically update via WebSocket events
  
  return (
    <div>
      {messages?.map(msg => (
        <div key={msg.id}>{msg.content}</div>
      ))}
    </div>
  );
}
```

## Available Hooks

### useWebSocketChat
Main hook for WebSocket chat functionality with real-time updates.

### useConversationMessages
React Query hook for fetching conversation messages with automatic cache invalidation.

### useConversations
React Query hook for fetching conversation list with automatic updates.

## Message Types

```typescript
interface WebSocketMessage {
  type: 'message_received' | 'typing' | 'token' | 'message_complete' | 'error' | 'chunk' | 'system';
  content?: string;
  conversation_id?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}
```

For complete documentation and examples, see the full service implementation.