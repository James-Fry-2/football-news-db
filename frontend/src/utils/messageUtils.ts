import { MessageUtils, UserMessage, BotMessage, ChatMessageType } from '@/types/chat';

export const messageUtils: MessageUtils = {
  formatTimestamp: (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    // Less than 1 minute ago
    if (diff < 60000) {
      return 'Just now';
    }
    
    // Less than 1 hour ago
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000);
      return `${minutes}m ago`;
    }
    
    // Less than 24 hours ago
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    }
    
    // Less than 7 days ago
    if (diff < 604800000) {
      const days = Math.floor(diff / 86400000);
      return `${days}d ago`;
    }
    
    // More than 7 days ago
    return date.toLocaleDateString();
  },

  formatRelativeTime: (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} days ago`;
    
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  },

  getMessageStatusIcon: (status: UserMessage['status'] | BotMessage['status']): string => {
    switch (status) {
      case 'sending':
      case 'generating':
        return '⏳';
      case 'sent':
      case 'complete':
        return '✓';
      case 'failed':
      case 'error':
        return '⚠️';
      default:
        return '';
    }
  },

  getMessageStatusColor: (status: UserMessage['status'] | BotMessage['status']): string => {
    switch (status) {
      case 'sending':
      case 'generating':
        return 'text-blue-500';
      case 'sent':
      case 'complete':
        return 'text-green-500';
      case 'failed':
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  },

  generateMessageId: (): string => {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  },

  validateMessage: (content: string): boolean => {
    if (!content || typeof content !== 'string') {
      return false;
    }
    
    const trimmedContent = content.trim();
    
    // Check if message is not empty
    if (trimmedContent.length === 0) {
      return false;
    }
    
    // Check if message is not too long (adjust as needed)
    if (trimmedContent.length > 4000) {
      return false;
    }
    
    // Check for basic content (not just whitespace or special characters)
    if (!/\w/.test(trimmedContent)) {
      return false;
    }
    
    return true;
  },
};

// Additional utility functions for message operations
export const createUserMessage = (
  content: string,
  conversationId?: string,
  status: UserMessage['status'] = 'sending'
): UserMessage => {
  return {
    id: messageUtils.generateMessageId(),
    type: 'user',
    sender: 'user',
    content: content.trim(),
    timestamp: new Date().toISOString(),
    conversation_id: conversationId,
    status,
  };
};

export const createBotMessage = (
  content: string,
  conversationId?: string,
  status: BotMessage['status'] = 'generating',
  isStreaming = false
): BotMessage => {
  return {
    id: messageUtils.generateMessageId(),
    type: 'assistant',
    sender: 'assistant',
    content: content.trim(),
    timestamp: new Date().toISOString(),
    conversation_id: conversationId,
    status,
    isStreaming,
  };
};

export const createSystemMessage = (
  content: string,
  level: 'info' | 'warning' | 'error' = 'info',
  conversationId?: string
) => {
  return {
    id: messageUtils.generateMessageId(),
    type: 'system' as const,
    sender: 'system' as const,
    content: content.trim(),
    timestamp: new Date().toISOString(),
    conversation_id: conversationId,
    level,
  };
};

export const createTypingIndicator = (conversationId?: string) => {
  return {
    id: messageUtils.generateMessageId(),
    type: 'typing' as const,
    sender: 'assistant' as const,
    timestamp: new Date().toISOString(),
    conversation_id: conversationId,
  };
};

// Message filtering and sorting utilities
export const filterMessagesByType = (messages: ChatMessageType[], type: ChatMessageType['type']) => {
  return messages.filter(message => message.type === type);
};

export const sortMessagesByTimestamp = (messages: ChatMessageType[], ascending = true) => {
  return [...messages].sort((a, b) => {
    const dateA = new Date(a.timestamp).getTime();
    const dateB = new Date(b.timestamp).getTime();
    return ascending ? dateA - dateB : dateB - dateA;
  });
};

export const getLatestMessage = (messages: ChatMessageType[]): ChatMessageType | null => {
  if (messages.length === 0) return null;
  return messages.reduce((latest, current) => {
    return new Date(current.timestamp) > new Date(latest.timestamp) ? current : latest;
  });
};

export const getMessageById = (messages: ChatMessageType[], id: string): ChatMessageType | null => {
  return messages.find(message => message.id === id) || null;
};

export const updateMessageStatus = (
  messages: ChatMessageType[],
  messageId: string,
  status: UserMessage['status'] | BotMessage['status']
): ChatMessageType[] => {
  return messages.map(message => {
    if (message.id === messageId) {
      if (message.type === 'user') {
        // Only allow user message statuses for user messages
        const userStatuses: UserMessage['status'][] = ['sending', 'sent', 'failed'];
        const validStatus = userStatuses.includes(status as UserMessage['status']) 
          ? status as UserMessage['status'] 
          : 'failed';
        return { ...message, status: validStatus } as UserMessage;
      } else if (message.type === 'assistant' || message.type === 'bot') {
        // Only allow bot message statuses for bot messages
        const botStatuses: BotMessage['status'][] = ['generating', 'complete', 'error'];
        const validStatus = botStatuses.includes(status as BotMessage['status']) 
          ? status as BotMessage['status'] 
          : 'error';
        return { ...message, status: validStatus } as BotMessage;
      }
    }
    return message;
  });
};

export const appendToStreamingMessage = (
  messages: ChatMessageType[],
  messageId: string,
  newContent: string
): ChatMessageType[] => {
  return messages.map(message => {
    if (message.id === messageId && (message.type === 'assistant' || message.type === 'bot')) {
      return {
        ...message,
        content: message.content + newContent,
        isStreaming: true,
      } as BotMessage;
    }
    return message;
  });
};

export const completeStreamingMessage = (
  messages: ChatMessageType[],
  messageId: string
): ChatMessageType[] => {
  return messages.map(message => {
    if (message.id === messageId && (message.type === 'assistant' || message.type === 'bot')) {
      return {
        ...message,
        status: 'complete' as const,
        isStreaming: false,
      } as BotMessage;
    }
    return message;
  });
};

// Content processing utilities
export const extractCodeBlocks = (content: string): { language: string; code: string }[] => {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const blocks: { language: string; code: string }[] = [];
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    blocks.push({
      language: match[1] || 'text',
      code: match[2].trim(),
    });
  }

  return blocks;
};

export const stripMarkdown = (content: string): string => {
  return content
    .replace(/\*\*(.*?)\*\*/g, '$1') // Bold
    .replace(/\*(.*?)\*/g, '$1') // Italic
    .replace(/`([^`]+)`/g, '$1') // Inline code
    .replace(/```[\s\S]*?```/g, '[Code Block]') // Code blocks
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Links
    .replace(/#{1,6}\s/g, '') // Headers
    .replace(/\n/g, ' ') // Line breaks
    .trim();
};

export const getWordCount = (content: string): number => {
  return stripMarkdown(content).split(/\s+/).filter(word => word.length > 0).length;
};

export const estimateReadingTime = (content: string, wordsPerMinute = 200): number => {
  const wordCount = getWordCount(content);
  return Math.max(1, Math.ceil(wordCount / wordsPerMinute));
}; 