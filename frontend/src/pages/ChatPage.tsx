import { useState, useEffect } from 'react';
import { Sidebar } from '../components/Sidebar';
import { MessageCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useWebSocketChat } from '../hooks/useWebSocketChat';
import { useConversationHistory } from '../hooks/useConversationHistory';
import { ChatContainer } from '../components/ChatContainer';
import { chatService } from '../services/chatService';

// Mock user for development
const mockUser = {
  id: 'user-123',
  name: 'Test User',
  email: 'test@example.com'
};

// Convert WebSocket messages to ChatContainer format
const convertWebSocketMessages = (wsMessages: any[]) => {
  const validMessages = wsMessages.filter(msg => 
    msg.id && 
    msg.content && 
    msg.content.trim() !== '' && 
    msg.timestamp &&
    msg.type !== 'ping' &&
    msg.type !== 'pong' &&
    msg.type !== 'system' &&
    msg.type !== 'typing'
  );

  return validMessages.map((msg) => ({
    id: msg.id,
    content: msg.content,
    timestamp: new Date(msg.timestamp),
    sender: msg.sender,
    type: msg.type || 'text',
    metadata: msg.metadata,
    status: msg.status || 'complete',
    isStreaming: msg.isStreaming || false,
  }));
};

export const ChatPage = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>();

  // WebSocket chat hook
  const {
    state: chatState,
    sendMessage,
    connect,
    joinConversation,
    leaveConversation,
    clearMessages,
    isReady,
    connectionId
  } = useWebSocketChat({
    conversationId: activeConversationId,
    autoConnect: true,
    enableRealtimeUpdates: true
  });

  // Conversation history hook
  const {
    conversations,
    loading: conversationsLoading,
    error: conversationsError,
    refetch: refetchConversations
  } = useConversationHistory(mockUser.id);

  // Set initial user ID in localStorage if not present
  useEffect(() => {
    if (!localStorage.getItem('userId')) {
      localStorage.setItem('userId', mockUser.id);
    }
  }, []);

  // Auto-hide sidebar on mobile
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsSidebarOpen(false);
      } else {
        setIsSidebarOpen(true);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Join/leave conversation when activeConversationId changes
  useEffect(() => {
    if (activeConversationId && chatState.isConnected) {
      joinConversation(activeConversationId);
      return () => {
        if (activeConversationId) {
          leaveConversation(activeConversationId);
        }
      };
    }
  }, [activeConversationId, chatState.isConnected, joinConversation, leaveConversation]);

  const handleConversationSelect = (conversationId: string) => {
    // Clear messages when switching conversations
    clearMessages();
    setActiveConversationId(conversationId);
    // Auto-close sidebar on mobile when selecting conversation
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  };

  const handleNewChat = () => {
    // Clear messages when starting new chat
    clearMessages();
    // Generate a new conversation ID
    const newConversationId = `chat-${Date.now()}`;
    setActiveConversationId(newConversationId);
    // Auto-close sidebar on mobile when starting new chat
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await chatService.deleteConversation(conversationId);
      // Refresh conversations list
      await refetchConversations();
      // If deleting the active conversation, clear it
      if (activeConversationId === conversationId) {
        setActiveConversationId(undefined);
        clearMessages();
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || !chatState.isConnected) return;

    try {
      // Send the message via WebSocket
      await sendMessage(message);
      // Refresh conversations list to update last message and timestamp
      setTimeout(async () => {
        await refetchConversations();
      }, 1000); // Small delay to ensure backend has processed the message
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error; // Re-throw to let ChatContainer handle it
    }
  };

  // Convert WebSocket messages for ChatContainer
  const convertedMessages = convertWebSocketMessages(chatState.messages);

  return (
    <div className="flex h-screen bg-background" style={{ height: 'calc(100vh - 4rem)' }}>
      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        activeConversationId={activeConversationId}
        onConversationSelect={handleConversationSelect}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        userId={mockUser.id}
        conversations={conversations}
        loading={conversationsLoading}
        error={conversationsError}
        onRefresh={refetchConversations}
      />

      {/* Main Chat Area */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${isSidebarOpen ? 'md:ml-0' : ''}`}>
        {activeConversationId ? (
          // Active conversation view
          <>
            {/* Chat Header */}
            <div className="border-b border-border p-4 bg-card">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-lg font-semibold">Chat Conversation</h1>
                  <p className="text-sm text-muted-foreground">
                    Conversation ID: {activeConversationId}
                  </p>
                  {/* WebSocket connection status */}
                  <div className="text-xs text-muted-foreground mt-1">
                    <span>WebSocket Status: </span>
                    {chatState.isConnecting && <span className="text-yellow-600">Connecting...</span>}
                    {chatState.isConnected && <span className="text-green-600">Connected</span>}
                    {!chatState.isConnected && !chatState.isConnecting && (
                      <span className="text-red-600">Disconnected</span>
                    )}
                    {connectionId && <span className="ml-2">({connectionId})</span>}
                  </div>
                  {chatState.error && (
                    <div className="text-xs text-red-600 mt-1">
                      Error: {chatState.error}
                    </div>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsSidebarOpen(true)}
                  className="md:hidden"
                >
                  <MessageCircle className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Chat Container */}
            <div className="flex-1 overflow-hidden">
              <ChatContainer
                messages={convertedMessages}
                onSendMessage={handleSendMessage}
                isLoading={chatState.isConnecting}
                placeholder="Type your message..."
                disabled={!chatState.isConnected}
                className="h-full"
                showHeader={false}
                enableAutoScroll={true}
                maxHeight="100%"
              />
            </div>
          </>
        ) : (
          // Welcome/No conversation selected view
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              <MessageCircle className="h-24 w-24 mx-auto mb-6 text-muted-foreground opacity-50" />
              <h1 className="text-2xl font-bold mb-2">Football News Chat</h1>
              <p className="text-muted-foreground mb-6">
                Ask questions about football news, players, teams, and get instant answers powered by AI.
              </p>
              <Button onClick={handleNewChat} size="lg" className="mb-4">
                <MessageCircle className="h-5 w-5 mr-2" />
                Start New Chat
              </Button>
              
              {/* Connection status info */}
              <div className="mt-6 p-3 bg-muted rounded text-left">
                <h4 className="font-medium text-sm mb-2">Connection Status:</h4>
                <div className="text-xs space-y-1">
                  <div>WebSocket: {chatState.isConnected ? '✅ Connected' : '❌ Disconnected'}</div>
                  <div>User ID: {mockUser.id}</div>
                  <div>Ready: {isReady ? '✅ Yes' : '❌ No'}</div>
                  {connectionId && <div>Connection ID: {connectionId}</div>}
                  {chatState.error && <div className="text-red-600">Error: {chatState.error}</div>}
                </div>
                {!chatState.isConnected && (
                  <Button 
                    onClick={connect} 
                    size="sm" 
                    variant="outline" 
                    className="mt-2"
                    disabled={chatState.isConnecting}
                  >
                    {chatState.isConnecting ? 'Connecting...' : 'Reconnect'}
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 