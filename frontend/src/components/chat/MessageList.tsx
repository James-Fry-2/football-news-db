import React, { useEffect, useRef, useState, useCallback } from 'react';
import { MessageListProps, ChatMessageType, UserMessage, BotMessage, SystemMessage } from '@/types/chat';
import { UserMessage as UserMessageComponent } from './UserMessage';
import { BotMessage as BotMessageComponent } from './BotMessage';
import { TypingAnimation } from './TypingAnimation';
import { cn } from '@/utils/cn';
import { AlertCircle, Info, AlertTriangle } from 'lucide-react';

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  loading,
  virtualization,
  showTimestamps = true,
  showAvatars = true,
  onRetryMessage,
  onEditMessage,
  onDeleteMessage,
  onSourceClick,
  className,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: messages.length });
  const [containerHeight, setContainerHeight] = useState(0);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current && virtualization?.scrollToBottom !== false) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [virtualization?.scrollToBottom]);

  useEffect(() => {
    if (virtualization?.autoScroll !== false) {
      scrollToBottom();
    }
  }, [messages.length, scrollToBottom, virtualization?.autoScroll]);

  // Virtualization logic
  useEffect(() => {
    if (!virtualization || !containerRef.current) return;

    const container = containerRef.current;
    const { height, itemHeight, overscan = 5 } = virtualization;

    const handleScroll = () => {
      const scrollTop = container.scrollTop;
      const startIndex = Math.floor(scrollTop / itemHeight);
      const endIndex = Math.min(
        startIndex + Math.ceil(height / itemHeight) + overscan,
        messages.length
      );

      setVisibleRange({
        start: Math.max(0, startIndex - overscan),
        end: endIndex,
      });
    };

    container.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial calculation

    return () => container.removeEventListener('scroll', handleScroll);
  }, [messages.length, virtualization]);

  // Update container height for virtualization
  useEffect(() => {
    if (virtualization && containerRef.current) {
      setContainerHeight(virtualization.height);
    }
  }, [virtualization]);

  const renderSystemMessage = (message: SystemMessage) => {
    const getIcon = () => {
      switch (message.level) {
        case 'error':
          return <AlertCircle className="h-4 w-4 text-red-500" />;
        case 'warning':
          return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
        case 'info':
        default:
          return <Info className="h-4 w-4 text-blue-500" />;
      }
    };

    const getBgColor = () => {
      switch (message.level) {
        case 'error':
          return 'bg-red-50 border-red-200 text-red-700';
        case 'warning':
          return 'bg-yellow-50 border-yellow-200 text-yellow-700';
        case 'info':
        default:
          return 'bg-blue-50 border-blue-200 text-blue-700';
      }
    };

    return (
      <div className={cn("flex justify-center mb-4", className)}>
        <div className={cn(
          "flex items-center space-x-2 px-3 py-2 rounded-lg border text-sm max-w-md",
          getBgColor()
        )}>
          {getIcon()}
          <span>{message.content}</span>
          {showTimestamps && (
            <span className="text-xs opacity-75">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>
    );
  };

  const renderTypingIndicator = () => {
    return (
      <div className={cn("flex mb-4", className)}>
        {showAvatars && (
          <div className="flex-shrink-0 mr-3">
            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
              <div className="w-4 h-4 bg-gray-400 rounded-full"></div>
            </div>
          </div>
        )}
        <div className="flex-1 max-w-[80%]">
          <TypingAnimation isTyping={true} />
        </div>
      </div>
    );
  };

  const renderMessage = (message: ChatMessageType, index: number) => {
    const key = `message-${message.id}-${index}`;

    switch (message.type) {
      case 'user':
        return (
          <UserMessageComponent
            key={key}
            message={message as UserMessage}
            showTimestamp={showTimestamps}
            onRetry={onRetryMessage}
            onEdit={onEditMessage}
            onDelete={onDeleteMessage}
          />
        );

      case 'bot':
      case 'assistant':
        return (
          <BotMessageComponent
            key={key}
            message={message as BotMessage}
            showTimestamp={showTimestamps}
            onSourceClick={onSourceClick}
            onRegenerateResponse={onRetryMessage}
          />
        );

      case 'system':
        return renderSystemMessage(message as SystemMessage);

      case 'typing':
        return renderTypingIndicator();

      default:
        return null;
    }
  };

  const renderLoadingState = () => {
    if (!loading?.isLoading) return null;

    return (
      <div className="flex justify-center py-4">
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          <span className="text-sm">
            {loading.isTyping ? 'Loading conversation history...' : 'Loading...'}
          </span>
        </div>
      </div>
    );
  };

  const renderErrorState = () => {
    if (!loading?.error) return null;

    return (
      <div className="flex justify-center py-4">
        <div className="flex items-center space-x-2 px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{loading.error}</span>
        </div>
      </div>
    );
  };

  if (virtualization) {
    const { height, itemHeight } = virtualization;
    const totalHeight = messages.length * itemHeight;
    const visibleMessages = messages.slice(visibleRange.start, visibleRange.end);

    return (
      <div
        ref={containerRef}
        className={cn("overflow-auto", className)}
        style={{ height }}
      >
        {/* Spacer for items above visible range */}
        <div style={{ height: visibleRange.start * itemHeight }} />
        
        {/* Visible messages */}
        <div>
          {renderLoadingState()}
          {renderErrorState()}
          {visibleMessages.map((message, index) => 
            renderMessage(message, visibleRange.start + index)
          )}
        </div>

        {/* Spacer for items below visible range */}
        <div style={{ height: Math.max(0, totalHeight - visibleRange.end * itemHeight) }} />
        
        <div ref={messagesEndRef} />
      </div>
    );
  }

  // Non-virtualized rendering
  return (
    <div 
      ref={containerRef}
      className={cn("flex flex-col space-y-1 overflow-auto", className)}
      style={virtualization ? { height: containerHeight } : undefined}
    >
      {renderLoadingState()}
      {renderErrorState()}
      
      {messages.map((message, index) => renderMessage(message, index))}
      
      {loading?.isTyping && (
        <div className="flex mb-4">
          {showAvatars && (
            <div className="flex-shrink-0 mr-3">
              <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                <div className="w-4 h-4 bg-gray-400 rounded-full"></div>
              </div>
            </div>
          )}
          <div className="flex-1 max-w-[80%]">
            <TypingAnimation isTyping={true} />
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
}; 