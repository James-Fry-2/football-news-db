import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, MessageCircle, Maximize2, Minimize2, MoreVertical } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';

// TypeScript interfaces
interface Message {
  id: string;
  content: string;
  timestamp: Date;
  sender: 'user' | 'assistant';
  type?: 'text' | 'system' | 'error';
}

interface ChatContainerProps {
  messages?: Message[];
  onSendMessage: (message: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
  onToggleSidebar?: () => void;
  showHeader?: boolean;
  headerContent?: React.ReactNode;
  disabled?: boolean;
  maxHeight?: string;
  enableAutoScroll?: boolean;
}

interface MessageItemProps {
  message: Message;
  className?: string;
}

interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onKeyPress: (e: React.KeyboardEvent) => void;
  placeholder: string;
  disabled: boolean;
  isLoading: boolean;
  className?: string;
}

// Message item component
const MessageItem: React.FC<MessageItemProps> = ({ message, className }) => {
  const isUser = message.sender === 'user';
  const isSystem = message.type === 'system';
  const isError = message.type === 'error';

  return (
    <div className={cn(
      "flex",
      isUser ? "justify-end" : "justify-start",
      isSystem && "justify-center",
      className
    )}>
      <div className={cn(
        "max-w-[80%] rounded-lg px-4 py-2 text-sm",
        isUser && "bg-primary text-primary-foreground ml-auto",
        !isUser && !isSystem && !isError && "bg-muted text-foreground",
        isSystem && "bg-accent text-accent-foreground text-xs max-w-[90%]",
        isError && "bg-destructive/10 text-destructive border border-destructive/20",
        "break-words"
      )}>
        <p className="whitespace-pre-wrap">{message.content}</p>
        <div className={cn(
          "text-xs mt-1 opacity-70",
          isUser ? "text-primary-foreground/70" : "text-muted-foreground"
        )}>
          {message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
};

// Message input component
const MessageInput: React.FC<MessageInputProps> = ({
  value,
  onChange,
  onSend,
  onKeyPress,
  placeholder,
  disabled,
  isLoading,
  className
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [value]);

  return (
    <div className={cn("flex items-end space-x-2", className)}>
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={cn(
            "w-full resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm",
            "ring-offset-background placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "min-h-[44px] max-h-[120px] transition-all duration-200"
          )}
          style={{ 
            minHeight: '44px',
            maxHeight: '120px',
            overflowY: value.split('\n').length > 3 ? 'auto' : 'hidden'
          }}
        />
      </div>
      <Button
        onClick={onSend}
        disabled={!value.trim() || isLoading || disabled}
        size="sm"
        className="h-11 px-3 shrink-0"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
};

// Main ChatContainer component
export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages = [],
  onSendMessage,
  isLoading = false,
  placeholder = "Type your message...",
  className,
  onToggleSidebar,
  showHeader = true,
  headerContent,
  disabled = false,
  maxHeight = '100vh',
  enableAutoScroll = true
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (enableAutoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, enableAutoScroll]);

  // Handle message sending
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || disabled) return;

    const messageText = inputValue.trim();
    setInputValue('');

    try {
      await onSendMessage(messageText);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Re-populate input on error
      setInputValue(messageText);
    }
  };

  // Handle keyboard shortcuts
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Toggle expanded view
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className={cn(
      "flex flex-col bg-background border border-border rounded-lg overflow-hidden",
      "transition-all duration-300 ease-in-out",
      isExpanded ? "fixed inset-4 z-50 shadow-2xl" : "relative",
      className
    )}
    style={{ 
      height: isExpanded ? 'calc(100vh - 2rem)' : maxHeight,
      maxHeight: isExpanded ? 'calc(100vh - 2rem)' : maxHeight
    }}
    >
      {/* Header */}
      {showHeader && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
          <div className="flex items-center space-x-2">
            {onToggleSidebar && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleSidebar}
                className="h-8 w-8 p-0 md:hidden"
              >
                <MessageCircle className="h-4 w-4" />
              </Button>
            )}
            {headerContent || (
              <div>
                <h3 className="text-sm font-medium">Chat</h3>
                <p className="text-xs text-muted-foreground">
                  {messages.length} message{messages.length !== 1 ? 's' : ''}
                </p>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleExpanded}
              className="h-8 w-8 p-0"
            >
              {isExpanded ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-4 scroll-smooth"
        style={{ 
          scrollBehavior: 'smooth',
          overscrollBehavior: 'contain'
        }}
      >
        {messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-center py-12">
            <div className="max-w-sm">
              <MessageCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="text-lg font-medium mb-2">No messages yet</h3>
              <p className="text-sm text-muted-foreground">
                Start a conversation by typing a message below.
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageItem
                key={message.id}
                message={message}
                className="animate-in slide-in-from-bottom-2 duration-300"
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-background/50 backdrop-blur-sm">
        <div className="p-4">
          <MessageInput
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSendMessage}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            isLoading={isLoading}
          />
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-muted-foreground">
              Press Enter to send, Shift+Enter for new line
            </p>
            {isLoading && (
              <p className="text-xs text-muted-foreground flex items-center">
                <Loader2 className="h-3 w-3 animate-spin mr-1" />
                Processing...
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Responsive grid layout wrapper
interface ChatGridProps {
  sidebar?: React.ReactNode;
  sidebarOpen?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const ChatGrid: React.FC<ChatGridProps> = ({
  sidebar,
  sidebarOpen = false,
  children,
  className
}) => {
  return (
    <div className={cn(
      "grid grid-cols-1 md:grid-cols-[300px_1fr] lg:grid-cols-[320px_1fr] gap-4",
      "h-[calc(100vh-4rem)] overflow-hidden",
      !sidebarOpen && "md:grid-cols-1",
      className
    )}>
      {/* Sidebar */}
      {sidebar && (
        <div className={cn(
          "transition-all duration-300 ease-in-out",
          sidebarOpen ? "block" : "hidden md:block",
          !sidebarOpen && "md:hidden"
        )}>
          {sidebar}
        </div>
      )}
      
      {/* Main Content */}
      <div className="min-w-0 flex flex-col">
        {children}
      </div>
    </div>
  );
};

// Default props
ChatContainer.displayName = 'ChatContainer';
ChatGrid.displayName = 'ChatGrid';

export type { 
  ChatContainerProps, 
  ChatGridProps, 
  Message, 
  MessageItemProps, 
  MessageInputProps 
}; 