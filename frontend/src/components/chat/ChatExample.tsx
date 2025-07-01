import React, { useState } from 'react';
import { EnhancedChatContainer } from './EnhancedChatContainer';
import { ChatMessageType, MessageSource } from '@/types/chat';
import { createUserMessage, createBotMessage } from '@/utils/messageUtils';

/**
 * Example usage of the chat components
 * This demonstrates how to integrate the EnhancedChatContainer
 * with proper error handling and event callbacks
 */
export const ChatExample: React.FC = () => {
  const [conversationId] = useState('example-conversation');
  
  // Example initial messages
  const initialMessages: ChatMessageType[] = [
    createUserMessage("Hello! Can you help me with football news?"),
    createBotMessage(
      "Hello! I'd be happy to help you with football news. I can search for the latest articles, provide analysis, and answer questions about teams and players. What would you like to know?",
      conversationId,
      'complete'
    ),
  ];

  const handleMessageSent = (message: string) => {
    console.log('Message sent:', message);
    // You can add analytics tracking here
  };

  const handleError = (error: string) => {
    console.error('Chat error:', error);
    // You can show toast notifications or handle errors here
  };

  const handleSourceClick = (source: MessageSource) => {
    console.log('Source clicked:', source);
    // Open source in new tab or show source details
    window.open(source.url, '_blank');
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Football News Chat</h1>
      
      <div className="bg-white rounded-lg shadow-lg">
        <EnhancedChatContainer
          conversationId={conversationId}
          initialMessages={initialMessages}
          height={600}
          enableVirtualization={true}
          autoConnect={true}
          showConnectionStatus={true}
          placeholder="Ask me about football news, teams, or players..."
          maxMessageLength={4000}
          onMessageSent={handleMessageSent}
          onError={handleError}
          onSourceClick={handleSourceClick}
          className="h-[600px]"
        />
      </div>

      <div className="mt-6 p-4 bg-gray-100 rounded-lg">
        <h2 className="font-semibold mb-2">Features Demonstrated:</h2>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Real-time chat with WebSocket connection</li>
          <li>• Message status indicators (sending, sent, failed)</li>
          <li>• Typing animations for bot responses</li>
          <li>• Message editing and deletion</li>
          <li>• Source citations with clickable links</li>
          <li>• Virtualized message list for performance</li>
          <li>• Connection status monitoring</li>
          <li>• Error handling and retry functionality</li>
          <li>• Markdown support in messages</li>
          <li>• Auto-scroll to latest messages</li>
        </ul>
      </div>
    </div>
  );
};

export default ChatExample; 