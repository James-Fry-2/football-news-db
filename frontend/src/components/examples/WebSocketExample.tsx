import React, { useState } from 'react';
import { useWebSocketChat, useConversationMessages } from '@/hooks/useWebSocketChat';
import { Button } from '@/components/ui/Button';

interface WebSocketExampleProps {
  conversationId?: string;
}

export const WebSocketExample: React.FC<WebSocketExampleProps> = ({
  conversationId = 'example-conversation'
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [streamingText, setStreamingText] = useState('');

  // Use the WebSocket chat hook
  const {
    state,
    sendMessage,
    connect,
    disconnect,
    isReady,
    connectionId,
    websocketService
  } = useWebSocketChat({
    conversationId,
    autoConnect: true,
    enableRealtimeUpdates: true,
  });

  // Use React Query hook for conversation messages
  const { data: conversationHistory, isLoading } = useConversationMessages(conversationId);

  // Handle streaming tokens
  React.useEffect(() => {
    if (!websocketService) return;

    const handleToken = (data: any) => {
      if (data.content) {
        setStreamingText(prev => prev + data.content);
      }
    };

    const handleMessageComplete = () => {
      setStreamingText('');
    };

    const handleError = (error: any) => {
      console.error('WebSocket error:', error);
    };

    websocketService.on('token', handleToken);
    websocketService.on('message_complete', handleMessageComplete);
    websocketService.on('error', handleError);

    return () => {
      websocketService.off('token', handleToken);
      websocketService.off('message_complete', handleMessageComplete);
      websocketService.off('error', handleError);
    };
  }, [websocketService]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !isReady) return;

    try {
      await sendMessage(inputMessage);
      setInputMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const getStatusColor = () => {
    if (state.isConnected) return 'bg-green-500';
    if (state.isConnecting) return 'bg-yellow-500';
    if (state.error) return 'bg-red-500';
    return 'bg-gray-500';
  };

  const getStatusText = () => {
    if (state.isConnected) return 'Connected';
    if (state.isConnecting) return 'Connecting...';
    if (state.error) return `Error: ${state.error}`;
    return 'Disconnected';
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">WebSocket Chat Example</h2>
      
      {/* Connection Status */}
      <div className="flex items-center gap-3 mb-4 p-3 bg-gray-50 rounded">
        <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />
        <span className="text-sm font-medium">{getStatusText()}</span>
        {connectionId && (
          <span className="text-xs text-gray-500">ID: {connectionId}</span>
        )}
        {state.connectionStatus.reconnectAttempts > 0 && (
          <span className="text-xs text-yellow-600">
            Reconnecting... (Attempt {state.connectionStatus.reconnectAttempts})
          </span>
        )}
      </div>

      {/* Connection Controls */}
      <div className="flex gap-2 mb-4">
        <Button 
          onClick={connect} 
          disabled={state.isConnected || state.isConnecting}
          size="sm"
        >
          Connect
        </Button>
        <Button 
          onClick={disconnect} 
          disabled={!state.isConnected}
          variant="outline"
          size="sm"
        >
          Disconnect
        </Button>
      </div>

      {/* Messages Display */}
      <div className="border rounded-lg p-4 h-64 overflow-y-auto mb-4 bg-gray-50">
        <h3 className="font-semibold mb-2">Messages:</h3>
        
        {/* Conversation History */}
        {isLoading && <div className="text-gray-500">Loading conversation...</div>}
        {conversationHistory?.map((msg: any, index: number) => (
          <div key={index} className="mb-2 p-2 bg-white rounded border">
            <div className="text-xs text-gray-500 mb-1">
              {msg.timestamp} - {msg.sender}
            </div>
            <div>{msg.content}</div>
          </div>
        ))}
        
        {/* Real-time Messages */}
        {state.messages.map((message, index) => (
          <div key={index} className="mb-2 p-2 bg-blue-50 rounded border border-blue-200">
            <div className="text-xs text-blue-600 mb-1">
              {message.timestamp} - {message.type}
            </div>
            <div className="text-blue-800">{message.content}</div>
          </div>
        ))}
        
        {/* Streaming Text */}
        {streamingText && (
          <div className="mb-2 p-2 bg-yellow-50 rounded border border-yellow-200">
            <div className="text-xs text-yellow-600 mb-1">Streaming...</div>
            <div className="text-yellow-800">
              {streamingText}
              <span className="animate-pulse">|</span>
            </div>
          </div>
        )}
      </div>

      {/* Message Input */}
      <form onSubmit={handleSendMessage} className="flex gap-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={!isReady}
        />
        <Button 
          type="submit" 
          disabled={!isReady || !inputMessage.trim()}
        >
          Send
        </Button>
      </form>

      {/* Debug Info */}
      <details className="mt-4">
        <summary className="cursor-pointer text-sm font-medium text-gray-600">
          Debug Information
        </summary>
        <div className="mt-2 p-3 bg-gray-100 rounded text-xs">
          <div><strong>Ready:</strong> {isReady ? 'Yes' : 'No'}</div>
          <div><strong>Connected:</strong> {state.isConnected ? 'Yes' : 'No'}</div>
          <div><strong>Connecting:</strong> {state.isConnecting ? 'Yes' : 'No'}</div>
          <div><strong>Connection ID:</strong> {connectionId || 'None'}</div>
          <div><strong>Error:</strong> {state.error || 'None'}</div>
          <div><strong>Reconnect Attempts:</strong> {state.connectionStatus.reconnectAttempts}</div>
          <div><strong>Message Count:</strong> {state.messages.length}</div>
          <div><strong>Conversation ID:</strong> {conversationId}</div>
        </div>
      </details>
    </div>
  );
};

export default WebSocketExample;