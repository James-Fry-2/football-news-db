import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, MessageCircle, Maximize2, Minimize2, MoreVertical, TrendingUp, Users, AlertTriangle, CheckCircle, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';

// Enhanced TypeScript interfaces for fantasy football
interface FantasyFootballData {
  players?: Array<{
    name: string;
    position: string;
    team: string;
    points: number;
    price: number;
    form: number;
    ownership: number;
  }>;
  teams?: Array<{
    name: string;
    fixture_difficulty: number;
    clean_sheet_probability: number;
  }>;
  transfers?: Array<{
    player_in: string;
    player_out: string;
    reason: string;
  }>;
  gameweek?: {
    number: number;
    deadline: string;
    captain_pick?: string;
  };
}

interface Message {
  id: string;
  content: string;
  timestamp: Date;
  sender: 'user' | 'assistant';
  type?: 'text' | 'system' | 'error' | 'fantasy_advice' | 'player_recommendation' | 'team_analysis';
  metadata?: {
    confidence?: number;
    sources?: Array<{ title: string; url: string; source: string }>;
    fantasy_data?: FantasyFootballData;
    tokens?: number;
    model?: string;
  };
  status?: 'sending' | 'sent' | 'generating' | 'complete' | 'error';
  isStreaming?: boolean;
}

interface ConnectionStatus {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  reconnectAttempts: number;
  lastPing?: Date;
  latency?: number;
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
  connectionStatus?: ConnectionStatus;
  isTyping?: boolean;
  typingUser?: string;
  onRetryConnection?: () => void;
}

interface MessageItemProps {
  message: Message;
  className?: string;
  onSourceClick?: (url: string) => void;
  onCopyContent?: (content: string) => void;
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
  isTyping?: boolean;
}

// Enhanced typing animation for fantasy football context
const TypingIndicator: React.FC<{ isTyping: boolean; typingUser?: string }> = ({ isTyping, typingUser }) => {
  if (!isTyping) return null;

  return (
    <div className="flex items-center space-x-2 px-4 py-2 text-sm text-muted-foreground">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-xs">
        {typingUser || 'Fantasy Assistant'} is analyzing your request...
      </span>
    </div>
  );
};

// Enhanced connection status indicator
const ConnectionIndicator: React.FC<{ 
  status: ConnectionStatus; 
  onRetry?: () => void 
}> = ({ status, onRetry }) => {
  const getStatusColor = () => {
    if (status.connected) return 'text-green-500';
    if (status.connecting) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getStatusIcon = () => {
    if (status.connected) return <Wifi className="h-3 w-3" />;
    if (status.connecting) return <Loader2 className="h-3 w-3 animate-spin" />;
    return <WifiOff className="h-3 w-3" />;
  };

  const getStatusText = () => {
    if (status.connected) return `Connected${status.latency ? ` (${status.latency}ms)` : ''}`;
    if (status.connecting) return 'Connecting...';
    return `Disconnected${status.reconnectAttempts > 0 ? ` (${status.reconnectAttempts} attempts)` : ''}`;
  };

  return (
    <div className="flex items-center space-x-2 text-xs">
      <div className={cn("flex items-center space-x-1", getStatusColor())}>
        {getStatusIcon()}
        <span>{getStatusText()}</span>
      </div>
      {!status.connected && !status.connecting && onRetry && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onRetry}
          className="h-6 px-2 text-xs"
        >
          Retry
        </Button>
      )}
    </div>
  );
};

// Enhanced fantasy football data rendering
const FantasyDataCard: React.FC<{ data: FantasyFootballData }> = ({ data }) => {
  if (!data) return null;

  return (
    <div className="mt-3 space-y-3 border rounded-lg p-3 bg-gradient-to-r from-green-50 to-blue-50">
      {/* Player recommendations */}
      {data.players && data.players.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold flex items-center mb-2">
            <Users className="h-4 w-4 mr-1 text-green-600" />
            Player Recommendations
          </h4>
          <div className="grid gap-2">
            {data.players.slice(0, 3).map((player, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-white rounded border">
                <div className="flex-1">
                  <span className="font-medium">{player.name}</span>
                  <span className="text-xs text-muted-foreground ml-2">
                    {player.position} • {player.team}
                  </span>
                </div>
                <div className="text-right text-xs space-y-1">
                  <div className="font-medium">£{player.price}m</div>
                  <div className="text-muted-foreground">{player.points} pts</div>
                </div>
                <div className={cn(
                  "ml-2 px-2 py-1 rounded text-xs font-medium",
                  player.form >= 4 ? "bg-green-100 text-green-800" : 
                  player.form >= 2 ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800"
                )}>
                  Form: {player.form}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transfer suggestions */}
      {data.transfers && data.transfers.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold flex items-center mb-2">
            <TrendingUp className="h-4 w-4 mr-1 text-blue-600" />
            Transfer Suggestions
          </h4>
          <div className="space-y-2">
            {data.transfers.map((transfer, index) => (
              <div key={index} className="p-2 bg-white rounded border">
                <div className="flex items-center text-sm">
                  <span className="text-red-600">Out: {transfer.player_out}</span>
                  <span className="mx-2">→</span>
                  <span className="text-green-600">In: {transfer.player_in}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{transfer.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gameweek info */}
      {data.gameweek && (
        <div className="p-2 bg-white rounded border">
          <h4 className="text-sm font-semibold mb-1">Gameweek {data.gameweek.number}</h4>
          <div className="text-xs text-muted-foreground space-y-1">
            <div>Deadline: {data.gameweek.deadline}</div>
            {data.gameweek.captain_pick && (
              <div className="flex items-center">
                <CheckCircle className="h-3 w-3 mr-1 text-green-500" />
                Captain suggestion: {data.gameweek.captain_pick}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Enhanced message item component with fantasy football formatting
const MessageItem: React.FC<MessageItemProps> = ({ message, className, onSourceClick, onCopyContent }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [copied, setCopied] = useState(false);
  
  const isUser = message.sender === 'user';
  const isSystem = message.type === 'system';
  const isError = message.type === 'error';
  const isFantasyAdvice = message.type === 'fantasy_advice' || message.type === 'player_recommendation' || message.type === 'team_analysis';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      onCopyContent?.(message.content);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getMessageIcon = () => {
    switch (message.type) {
      case 'fantasy_advice':
        return <TrendingUp className="h-3 w-3 text-green-600" />;
      case 'player_recommendation':
        return <Users className="h-3 w-3 text-blue-600" />;
      case 'team_analysis':
        return <MessageCircle className="h-3 w-3 text-purple-600" />;
      case 'error':
        return <AlertTriangle className="h-3 w-3 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusIndicator = () => {
    if (message.status === 'generating' || message.isStreaming) {
      return <Loader2 className="h-3 w-3 animate-spin text-blue-500" />;
    }
    if (message.status === 'error') {
      return <AlertTriangle className="h-3 w-3 text-red-500" />;
    }
    if (message.status === 'complete') {
      return <CheckCircle className="h-3 w-3 text-green-500" />;
    }
    return null;
  };

  return (
    <div 
      className={cn(
        "flex",
        isUser ? "justify-start" : "justify-end",
        isSystem && "justify-center",
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={cn(
        "max-w-[85%] rounded-lg px-4 py-3 text-sm relative group",
        isUser && "bg-primary text-primary-foreground mr-auto",
        !isUser && !isSystem && !isError && "bg-muted text-foreground ml-auto",
        isSystem && "bg-accent text-accent-foreground text-xs max-w-[90%]",
        isError && "bg-destructive/10 text-destructive border border-destructive/20",
        isFantasyAdvice && "bg-gradient-to-r from-green-50 to-blue-50 border border-green-200",
        "break-words transition-all duration-200"
      )}>
        {/* Message header for fantasy advice */}
        {isFantasyAdvice && (
          <div className="flex items-center space-x-2 mb-2 pb-2 border-b border-green-200">
            {getMessageIcon()}
            <span className="text-xs font-medium text-green-700">
              {message.type === 'fantasy_advice' && 'Fantasy Advice'}
              {message.type === 'player_recommendation' && 'Player Recommendations'}
              {message.type === 'team_analysis' && 'Team Analysis'}
            </span>
            {message.metadata?.confidence && (
              <span className="text-xs text-muted-foreground">
                {Math.round(message.metadata.confidence * 100)}% confidence
              </span>
            )}
          </div>
        )}

        {/* Message content */}
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* Fantasy football data visualization */}
        {message.metadata?.fantasy_data && (
          <FantasyDataCard data={message.metadata.fantasy_data} />
        )}

        {/* Sources */}
        {message.metadata?.sources && message.metadata.sources.length > 0 && (
          <div className="mt-3 pt-2 border-t border-border/50">
            <p className="text-xs text-muted-foreground mb-2">Sources:</p>
            <div className="space-y-1">
              {message.metadata.sources.slice(0, 3).map((source, index) => (
                <button
                  key={index}
                  onClick={() => onSourceClick?.(source.url)}
                  className="block text-xs text-blue-600 hover:text-blue-800 hover:underline text-left truncate max-w-full"
                >
                  {source.title} • {source.source}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message footer */}
        <div className="flex items-center justify-between mt-2 pt-2">
          <div className={cn(
            "text-xs opacity-70 flex items-center space-x-2",
            isUser ? "text-primary-foreground/70" : "text-muted-foreground"
          )}>
            <span>
              {message.timestamp.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </span>
            {getStatusIndicator()}
            {message.metadata?.tokens && (
              <span className="text-xs opacity-50">{message.metadata.tokens} tokens</span>
            )}
          </div>

          {/* Copy button */}
          {isHovered && !isUser && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              {copied ? (
                <CheckCircle className="h-3 w-3 text-green-500" />
              ) : (
                <MessageCircle className="h-3 w-3" />
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

// Enhanced message input component
const MessageInput: React.FC<MessageInputProps> = ({
  value,
  onChange,
  onSend,
  onKeyPress,
  placeholder,
  disabled,
  isLoading,
  className,
  isTyping
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isFocused, setIsFocused] = useState(false);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [value]);

  // Fantasy football quick suggestions
  const quickSuggestions = [
    "Who should I captain this week?",
    "Best budget defenders?", 
    "Transfer recommendations?",
    "Analyze my team"
  ];

  const [showSuggestions, setShowSuggestions] = useState(false);

  return (
    <div className={cn("space-y-2", className)}>
      {/* Quick suggestions */}
      {showSuggestions && value === '' && (
        <div className="flex flex-wrap gap-2">
          {quickSuggestions.map((suggestion, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => onChange(suggestion)}
              className="text-xs h-7"
            >
              {suggestion}
            </Button>
          ))}
        </div>
      )}

      <div className="flex items-end space-x-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyPress={onKeyPress}
            onFocus={() => {
              setIsFocused(true);
              setShowSuggestions(true);
            }}
            onBlur={() => {
              setIsFocused(false);
              setTimeout(() => setShowSuggestions(false), 150);
            }}
            placeholder={placeholder}
            disabled={disabled || isTyping}
            rows={1}
            className={cn(
              "w-full resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm",
              "ring-offset-background placeholder:text-muted-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "min-h-[44px] max-h-[120px] transition-all duration-200",
              isFocused && "ring-2 ring-ring ring-offset-2",
              isTyping && "bg-muted"
            )}
            style={{ 
              minHeight: '44px',
              maxHeight: '120px',
              overflowY: value.split('\n').length > 3 ? 'auto' : 'hidden'
            }}
          />
          
          {/* Character counter for long messages */}
          {value.length > 500 && (
            <div className="absolute bottom-1 right-1 text-xs text-muted-foreground">
              {value.length}/2000
            </div>
          )}
        </div>
        
        <Button
          onClick={onSend}
          disabled={!value.trim() || isLoading || disabled || isTyping}
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
    </div>
  );
};

// Main ChatContainer component with enhanced features
export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages = [],
  onSendMessage,
  isLoading = false,
  placeholder = "Ask about your fantasy team, player suggestions, or gameweek strategy...",
  className,
  onToggleSidebar,
  showHeader = true,
  headerContent,
  disabled = false,
  maxHeight = '100vh',
  enableAutoScroll = true,
  connectionStatus = { connected: true, connecting: false, error: null, reconnectAttempts: 0 },
  isTyping = false,
  typingUser,
  onRetryConnection
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [lastActivity, setLastActivity] = useState<Date>(new Date());

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (enableAutoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, enableAutoScroll, isTyping]);

  // Update last activity
  useEffect(() => {
    if (messages.length > 0) {
      setLastActivity(new Date());
    }
  }, [messages]);

  // Enhanced message sending with error handling and retry logic
  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading || disabled || isTyping) return;

    const messageText = inputValue.trim();
    setInputValue('');

    try {
      await onSendMessage(messageText);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Re-populate input on error for retry
      setInputValue(messageText);
      
      // Show error notification (could be enhanced with toast)
      if (error instanceof Error) {
        console.error('Chat error:', error.message);
      }
    }
  }, [inputValue, isLoading, disabled, isTyping, onSendMessage]);

  // Handle keyboard shortcuts
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  // Toggle expanded view
  const toggleExpanded = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);

  // Handle source clicks
  const handleSourceClick = useCallback((url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  }, []);

  // Handle content copy
  const handleCopyContent = useCallback((content: string) => {
    console.log('Content copied:', content.substring(0, 50) + '...');
  }, []);

  return (
    <div className={cn(
      "flex flex-col bg-background border border-border rounded-lg overflow-hidden",
      "transition-all duration-300 ease-in-out shadow-sm",
      isExpanded ? "fixed inset-4 z-50 shadow-2xl" : "relative",
      !connectionStatus.connected && "border-red-200 bg-red-50/30",
      className
    )}
    style={{ 
      height: isExpanded ? 'calc(100vh - 2rem)' : maxHeight,
      maxHeight: isExpanded ? 'calc(100vh - 2rem)' : maxHeight
    }}
    >
      {/* Enhanced Header */}
      {showHeader && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
          <div className="flex items-center space-x-3">
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
              <div className="flex items-center space-x-3">
                <div>
                  <h3 className="text-sm font-medium flex items-center">
                    <TrendingUp className="h-4 w-4 mr-2 text-green-600" />
                    Fantasy Football Assistant
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    {messages.length} message{messages.length !== 1 ? 's' : ''} • 
                    Last active {lastActivity.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                
                <ConnectionIndicator 
                  status={connectionStatus} 
                  onRetry={onRetryConnection}
                />
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleExpanded}
              className="h-8 w-8 p-0"
              title={isExpanded ? "Minimize chat" : "Expand chat"}
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
              title="Chat options"
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
              <TrendingUp className="h-16 w-16 mx-auto mb-4 text-green-500 opacity-50" />
              <h3 className="text-lg font-medium mb-2">Welcome to Fantasy Football Assistant</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Get personalized advice, player recommendations, and team analysis to dominate your fantasy league.
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 bg-green-50 rounded border">
                  <div className="font-medium">Player Analysis</div>
                  <div className="text-muted-foreground">Form, fixtures, value</div>
                </div>
                <div className="p-2 bg-blue-50 rounded border">
                  <div className="font-medium">Transfer Tips</div>
                  <div className="text-muted-foreground">Smart moves, timing</div>
                </div>
                <div className="p-2 bg-purple-50 rounded border">
                  <div className="font-medium">Captain Picks</div>
                  <div className="text-muted-foreground">Weekly recommendations</div>
                </div>
                <div className="p-2 bg-orange-50 rounded border">
                  <div className="font-medium">Team Strategy</div>
                  <div className="text-muted-foreground">Formation, bench</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages
              .filter(message => 
                message.content && 
                message.content.trim() !== '' && 
                message.id && 
                message.timestamp
              )
              .map((message) => (
                <MessageItem
                  key={message.id}
                  message={message}
                  className="animate-in slide-in-from-bottom-2 duration-300"
                  onSourceClick={handleSourceClick}
                  onCopyContent={handleCopyContent}
                />
              ))}
            
            {/* Typing indicator */}
            {isTyping && <TypingIndicator isTyping={isTyping} typingUser={typingUser} />}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Enhanced Input Area */}
      <div className="border-t border-border bg-background/50 backdrop-blur-sm">
        <div className="p-4">
          <MessageInput
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSendMessage}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled || !connectionStatus.connected}
            isLoading={isLoading}
            isTyping={isTyping}
          />
          
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center space-x-4">
              <p className="text-xs text-muted-foreground">
                Press Enter to send, Shift+Enter for new line
              </p>
              {!connectionStatus.connected && (
                <p className="text-xs text-red-500 flex items-center">
                  <WifiOff className="h-3 w-3 mr-1" />
                  Connection lost
                </p>
              )}
            </div>
            
            {(isLoading || isTyping) && (
              <p className="text-xs text-muted-foreground flex items-center">
                <Loader2 className="h-3 w-3 animate-spin mr-1" />
                {isTyping ? 'Analyzing...' : 'Processing...'}
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