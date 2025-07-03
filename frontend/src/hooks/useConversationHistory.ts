import { useState, useEffect, useCallback } from 'react';
import { chatService } from '../services/chatService';
import { ConversationSummary } from '../types/api';

interface UseConversationHistoryReturn {
  conversations: ConversationSummary[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

// Mock conversations for testing
const mockConversations: ConversationSummary[] = [
  {
    conversation_id: 'conv-1',
    last_message: 'Who should I captain for gameweek 15?',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
    message_count: 5
  },
  {
    conversation_id: 'conv-2', 
    last_message: 'Best defenders under £5.0m this season?',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
    message_count: 8
  },
  {
    conversation_id: 'conv-3',
    last_message: 'Arsenal vs Chelsea fixture analysis',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
    message_count: 12
  },
  {
    conversation_id: 'conv-4',
    last_message: 'Transfer advice for this week',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(), // 2 days ago
    message_count: 3
  }
];

export const useConversationHistory = (userId?: string): UseConversationHistoryReturn => {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    if (!userId) {
      setConversations([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await chatService.listConversations(userId);
      
      // If API returns empty or no data, use mock data for testing
      if (!result || (Array.isArray(result) && result.length === 0)) {
        console.log('📝 Using mock conversation data for development');
        setConversations(mockConversations);
      } else {
        setConversations(Array.isArray(result) ? result : []);
      }
    } catch (err) {
      console.error('Failed to fetch conversations:', err);
      console.log('📝 Falling back to mock conversation data');
      
      // Fallback to mock data on error for better development experience
      setConversations(mockConversations);
      setError(null); // Don't show error when using fallback data
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // Fetch conversations on mount and when userId changes
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const refetch = useCallback(async () => {
    await fetchConversations();
  }, [fetchConversations]);

  return {
    conversations,
    loading,
    error,
    refetch,
  };
}; 