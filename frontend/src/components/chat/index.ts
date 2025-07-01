// Chat message components
export { UserMessage } from './UserMessage';
export { BotMessage } from './BotMessage';
export { TypingAnimation } from './TypingAnimation';

// Message list and container components
export { MessageList } from './MessageList';
export { EnhancedChatContainer } from './EnhancedChatContainer';

// Re-export types for convenience
export type {
  ChatMessageType,
  UserMessage as UserMessageType,
  BotMessage as BotMessageType,
  SystemMessage,
  TypingIndicator,
  MessageSource,
  MessageLoadingState,
  ChatLoadingState,
  ChatError,
  UserMessageProps,
  BotMessageProps,
  MessageListProps,
  TypingAnimationProps,
} from '@/types/chat'; 