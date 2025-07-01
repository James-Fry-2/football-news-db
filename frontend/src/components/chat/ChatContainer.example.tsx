import React, { useState } from 'react';
import { ChatContainer, ChatGrid, Message } from '../ChatContainer';
import { Sidebar } from '../Sidebar';

// Example usage of ChatContainer with ChatGrid
export const ChatExample: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! How can I help you with football news today?',
      timestamp: new Date(Date.now() - 60000),
      sender: 'assistant',
      type: 'text'
    },
    {
      id: '2',
      content: 'I\'d like to know about the latest Premier League transfers.',
      timestamp: new Date(Date.now() - 30000),
      sender: 'user',
      type: 'text'
    }
  ]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Mock user for sidebar
  const mockUser = {
    id: 'user-123',
    name: 'Test User',
    email: 'test@example.com'
  };

  // Handle sending new messages
  const handleSendMessage = async (content: string) => {
    setIsLoading(true);
    
    // Add user message immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      timestamp: new Date(),
      sender: 'user',
      type: 'text'
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `I received your message: "${content}". Here's a response about football news and transfers.`,
        timestamp: new Date(),
        sender: 'assistant',
        type: 'text'
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        sender: 'assistant',
        type: 'error'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle sidebar actions
  const handleConversationSelect = (conversationId: string) => {
    console.log('Selected conversation:', conversationId);
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  const handleDeleteConversation = (conversationId: string) => {
    console.log('Delete conversation:', conversationId);
  };

  return (
    <div className="h-screen bg-background">
      <ChatGrid
        sidebar={
          <Sidebar
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            activeConversationId="current-chat"
            onConversationSelect={handleConversationSelect}
            onNewChat={handleNewChat}
            onDeleteConversation={handleDeleteConversation}
            userId={mockUser.id}
          />
        }
        sidebarOpen={sidebarOpen}
      >
        <ChatContainer
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          placeholder="Ask about football news, players, transfers..."
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          headerContent={
            <div>
              <h3 className="text-sm font-medium">Football News Chat</h3>
              <p className="text-xs text-muted-foreground">
                Get instant answers about football
              </p>
            </div>
          }
        />
      </ChatGrid>
    </div>
  );
};

// Standalone ChatContainer example (without sidebar)
export const SimpleChatExample: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (content: string) => {
    setIsLoading(true);
    
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      timestamp: new Date(),
      sender: 'user'
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // Simulate response
    setTimeout(() => {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        content: `Echo: ${content}`,
        timestamp: new Date(),
        sender: 'assistant'
      };
      
      setMessages(prev => [...prev, response]);
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="p-4 h-screen bg-background">
      <div className="max-w-4xl mx-auto h-full">
        <ChatContainer
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          placeholder="Type a message..."
          maxHeight="calc(100vh - 2rem)"
        />
      </div>
    </div>
  );
}; 