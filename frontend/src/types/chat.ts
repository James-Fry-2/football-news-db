// Enhanced chat message types with loading states and error handling

export interface BaseMessage {
  id: string;
  content: string;
  timestamp: string;
  conversation_id?: string;
}

export interface UserMessage extends BaseMessage {
  type: 'user';
  sender: 'user';
  status: 'sending' | 'sent' | 'failed';
  edited?: boolean;
  editedAt?: string;
}

export interface BotMessage extends BaseMessage {
  type: 'bot' | 'assistant';
  sender: 'assistant';
  status: 'generating' | 'complete' | 'error';
  isStreaming?: boolean;
  metadata?: {
    sources?: MessageSource[];
    reasoning?: string;
    confidence?: number;
    model?: string;
    tokens?: number;
  };
}

export interface SystemMessage extends BaseMessage {
  type: 'system';
  sender: 'system';
  level: 'info' | 'warning' | 'error';
}

export interface TypingIndicator {
  id: string;
  type: 'typing';
  sender: 'assistant';
  timestamp: string;
  conversation_id?: string;
}

export type ChatMessageType = UserMessage | BotMessage | SystemMessage | TypingIndicator;

export interface MessageSource {
  id: string;
  title: string;
  url: string;
  source: string;
  published_date?: string;
  relevance_score?: number;
  excerpt?: string;
}

// Loading states
export interface MessageLoadingState {
  isLoading: boolean;
  isStreaming: boolean;
  isTyping: boolean;
  error: string | null;
  progress?: number; // 0-100 for streaming progress
}

export interface ChatLoadingState {
  isConnecting: boolean;
  isConnected: boolean;
  isSending: boolean;
  isLoadingHistory: boolean;
  error: string | null;
  lastActivity?: string;
}

// Error types
export interface ChatError {
  type: 'connection' | 'send' | 'receive' | 'validation' | 'timeout';
  message: string;
  code?: string;
  timestamp: string;
  retryable: boolean;
}

// Message list virtualization
export interface VirtualizedMessageProps {
  height: number;
  itemHeight: number;
  overscan?: number;
  scrollToBottom?: boolean;
  autoScroll?: boolean;
}

// Component props interfaces
export interface UserMessageProps {
  message: UserMessage;
  showTimestamp?: boolean;
  showStatus?: boolean;
  onRetry?: (messageId: string) => void;
  onEdit?: (messageId: string, newContent: string) => void;
  onDelete?: (messageId: string) => void;
  className?: string;
}

export interface BotMessageProps {
  message: BotMessage;
  showTimestamp?: boolean;
  showSources?: boolean;
  onSourceClick?: (source: MessageSource) => void;
  onCopy?: (content: string) => void;
  onRegenerateResponse?: (messageId: string) => void;
  className?: string;
}

export interface MessageListProps {
  messages: ChatMessageType[];
  loading?: MessageLoadingState;
  virtualization?: VirtualizedMessageProps;
  showTimestamps?: boolean;
  showAvatars?: boolean;
  onRetryMessage?: (messageId: string) => void;
  onEditMessage?: (messageId: string, newContent: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  onSourceClick?: (source: MessageSource) => void;
  className?: string;
}

export interface TypingAnimationProps {
  isTyping: boolean;
  duration?: number;
  className?: string;
}

// Markdown rendering options
export interface MarkdownOptions {
  enableSyntaxHighlighting?: boolean;
  enableMath?: boolean;
  enableTables?: boolean;
  enableBreaks?: boolean;
  sanitize?: boolean;
  customRenderers?: Record<string, any>;
}

// Message utils
export interface MessageUtils {
  formatTimestamp: (timestamp: string) => string;
  formatRelativeTime: (timestamp: string) => string;
  getMessageStatusIcon: (status: UserMessage['status'] | BotMessage['status']) => string;
  getMessageStatusColor: (status: UserMessage['status'] | BotMessage['status']) => string;
  generateMessageId: () => string;
  validateMessage: (content: string) => boolean;
}

// Conversation metadata
export interface ConversationMetadata {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  participants: string[];
  tags?: string[];
  archived?: boolean;
} 