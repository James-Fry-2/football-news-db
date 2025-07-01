import React, { useState, useEffect, useCallback } from 'react';
import { Send, Loader2, AlertCircle, Wifi, WifiOff } from 'lucide-react';
import { MessageList } from './MessageList';

import { useWebSocketChat } from '@/hooks/useWebSocketChat';
import { 
  ChatMessageType, 
  MessageLoadingState, 
  MessageSource,
  UserMessage,
  BotMessage 
} from '@/types/chat';
import { 
  createUserMessage, 

  createSystemMessage,
  messageUtils 
} from '@/utils/messageUtils';
import { cn } from '@/utils/cn';

interface EnhancedChatContainerProps {
  conversationId?: string;
  initialMessages?: ChatMessageType[];
  height?: number;
  enableVirtualization?: boolean;
  autoConnect?: boolean;
  showConnectionStatus?: boolean;
  placeholder?: string;
  maxMessageLength?: number;
  className?: string;
  onMessageSent?: (message: string) => void;
  onError?: (error: string) => void;
  onSourceClick?: (source: MessageSource) => void;
}

export const EnhancedChatContainer: React.FC<EnhancedChatContainerProps> = ({
  conversationId,
  initialMessages = [],
  height = 600,
  enableVirtualization = true,
  autoConnect = true,
  showConnectionStatus = true,
  placeholder = "Type your message...",
  maxMessageLength = 4000,
  className,
  onMessageSent,
  onError,
  onSourceClick,
}) => {
  const [localMessages, setLocalMessages] = useState<ChatMessageType[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isComposing, setIsComposing] = useState(false);

  // WebSocket chat hook
  const {
    state: chatState,
    sendMessage,
    connect,

  } = useWebSocketChat({
    conversationId,
    autoConnect,
    enableRealtimeUpdates: true,
  });

  // Merge WebSocket messages with local messages
  useEffect(() => {
    if (chatState.messages.length > 0) {
      setLocalMessages((prev: ChatMessageType[]) => {
        const newMessages = [...prev];
        
        // Add new messages from WebSocket that aren't already in local state
        chatState.messages.forEach(wsMessage => {
          const exists = newMessages.some(msg => msg.id === wsMessage.id);
          if (!exists) {
            // Convert WebSocket message to our chat message format
            if (wsMessage.sender === 'user') {
              const userMessage: UserMessage = {
                id: wsMessage.id || messageUtils.generateMessageId(),
                type: 'user',
                sender: 'user',
                content: wsMessage.content || '',
                timestamp: wsMessage.timestamp || new Date().toISOString(),
                conversation_id: wsMessage.conversation_id,
                status: 'sent',
              };
              newMessages.push(userMessage);
            } else if (wsMessage.sender === 'assistant') {
              const botMessage: BotMessage = {
                id: wsMessage.id || messageUtils.generateMessageId(),
                type: 'assistant',
                sender: 'assistant',
                content: wsMessage.content || '',
                timestamp: wsMessage.timestamp || new Date().toISOString(),
                conversation_id: wsMessage.conversation_id,
                status: wsMessage.type === 'token' ? 'generating' : 'complete',
                isStreaming: wsMessage.type === 'token',
              };
              newMessages.push(botMessage);
            }
          }
        });
        
        return newMessages.sort((a, b) => 
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        );
      });
    }
  }, [chatState.messages]);

  // Handle connection errors
  useEffect(() => {
    if (chatState.error && onError) {
      onError(chatState.error);
    }
  }, [chatState.error, onError]);

  // Loading state for message list
  const messageLoadingState: MessageLoadingState = {
    isLoading: chatState.isConnecting,
    isStreaming: localMessages.some((msg: ChatMessageType) => 
      (msg.type === 'assistant' || msg.type === 'bot') && 
      (msg as BotMessage).isStreaming
    ),
    isTyping: chatState.isConnecting,
    error: chatState.error,
  };

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || !messageUtils.validateMessage(inputValue) || isComposing) {
      return;
    }

    const messageContent = inputValue.trim();
    setIsComposing(true);
    setInputValue('');

    try {
      // Add user message to local state immediately
      const userMessage = createUserMessage(messageContent, conversationId, 'sending');
      setLocalMessages((prev: ChatMessageType[]) => [...prev, userMessage]);

      // Send through WebSocket
      await sendMessage(messageContent);

      // Update message status to sent
      setLocalMessages((prev: ChatMessageType[]) => 
        prev.map((msg: ChatMessageType) => {
          if (msg.id === userMessage.id && msg.type === 'user') {
            return { ...msg, status: 'sent' as const };
          }
          return msg;
        })
      );

      onMessageSent?.(messageContent);
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Update message status to failed and show error
      setLocalMessages((prev: ChatMessageType[]) => 
        prev.map((msg: ChatMessageType) => {
          if (msg.type === 'user' && msg.content === messageContent && msg.status === 'sending') {
            return { ...msg, status: 'failed' as const };
          }
          return msg;
        })
      );

      // Add system error message
      const errorMessage = createSystemMessage(
        'Failed to send message. Please try again.',
        'error',
        conversationId
      );
      setLocalMessages((prev: ChatMessageType[]) => [...prev, errorMessage]);
      
      onError?.('Failed to send message');
    } finally {
      setIsComposing(false);
    }
  }, [inputValue, conversationId, sendMessage, onMessageSent, onError, isComposing]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleRetryMessage = useCallback((messageId: string) => {
    const message = localMessages.find(msg => msg.id === messageId);
    if (message && message.type === 'user') {
      // Retry by resending the message
      setInputValue(message.content);
      handleSendMessage();
    }
  }, [localMessages, handleSendMessage]);

  const handleEditMessage = useCallback((messageId: string, newContent: string) => {
    setLocalMessages((prev: ChatMessageType[]) => 
      prev.map((msg: ChatMessageType) => {
        if (msg.id === messageId && msg.type === 'user') {
          return { 
            ...msg, 
            content: newContent,
            edited: true,
            editedAt: new Date().toISOString()
          };
        }
        return msg;
      })
    );
  }, []);

  const handleDeleteMessage = useCallback((messageId: string) => {
    setLocalMessages((prev: ChatMessageType[]) => prev.filter(msg => msg.id !== messageId));
  }, []);

  const renderConnectionStatus = () => {
    if (!showConnectionStatus) return null;

    return (
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-2">
          {chatState.isConnected ? (
            <>
              <Wifi className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-700">Connected</span>
            </>
          ) : chatState.isConnecting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
              <span className="text-sm text-blue-700">Connecting...</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-700">Disconnected</span>
              <button
                onClick={connect}
                className="ml-2 text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
              >
                Reconnect
              </button>
            </>
          )}
        </div>
        
        {chatState.error && (
          <div className="flex items-center space-x-1 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-xs">{chatState.error}</span>
          </div>
        )}
      </div>
    );
  };

  const renderMessageInput = () => {
    const isDisabled = !chatState.isConnected || isComposing;
    const isOverLimit = inputValue.length > maxMessageLength;

    return (
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-3">
          <div className="flex-1">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isDisabled ? "Connecting..." : placeholder}
              disabled={isDisabled}
              className={cn(
                "w-full px-3 py-2 border border-gray-300 rounded-lg resize-none",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "disabled:bg-gray-100 disabled:cursor-not-allowed",
                isOverLimit && "border-red-500 focus:ring-red-500"
              )}
              rows={Math.min(4, Math.max(1, inputValue.split('\n').length))}
            />
            <div className="flex justify-between mt-1">
              <div className="text-xs text-gray-500">
                {isOverLimit && (
                  <span className="text-red-500">
                    Message too long ({inputValue.length}/{maxMessageLength})
                  </span>
                )}
              </div>
              <div className="text-xs text-gray-500">
                {inputValue.length}/{maxMessageLength}
              </div>
            </div>
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={isDisabled || !inputValue.trim() || isOverLimit}
            className={cn(
              "px-4 py-2 bg-blue-600 text-white rounded-lg transition-all",
              "hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500",
              "disabled:bg-gray-300 disabled:cursor-not-allowed",
              "flex items-center space-x-2"
            )}
          >
            {isComposing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className={cn("flex flex-col bg-white border border-gray-200 rounded-lg shadow-sm", className)}>
      {renderConnectionStatus()}
      
      <div className="flex-1" style={{ height: height - 120 }}>
        <MessageList
          messages={localMessages}
          loading={messageLoadingState}
          virtualization={enableVirtualization ? {
            height: height - 120,
            itemHeight: 100,
            overscan: 5,
            scrollToBottom: true,
            autoScroll: true,
          } : undefined}
          showTimestamps={true}
          showAvatars={true}
          onRetryMessage={handleRetryMessage}
          onEditMessage={handleEditMessage}
          onDeleteMessage={handleDeleteMessage}
          onSourceClick={onSourceClick}
          className="p-4"
        />
      </div>
      
      {renderMessageInput()}
    </div>
  );
}; 