import { useState, useEffect, useRef } from 'react';
import { 
  MessageCircle, 
  Plus, 
  MoreVertical,
  ChevronLeft,
  Search,
  Clock,
  Trash2,
  X
} from 'lucide-react';
import { Button } from './ui/Button';
import { cn } from '@/utils/cn';
import { ConversationSummary } from '@/types/api';

// TypeScript interfaces
interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  activeConversationId?: string;
  onConversationSelect: (conversationId: string) => void;
  onNewChat: () => void;
  onDeleteConversation: (conversationId: string) => void;
  className?: string;
  userId?: string;
  // New props for external data management
  conversations?: ConversationSummary[];
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

interface ConversationItemProps {
  conversation: ConversationSummary;
  isActive: boolean;
  onSelect: (conversationId: string) => void;
  onDelete: (conversationId: string) => void;
}

interface ConversationMenuProps {
  conversationId: string;
  onDelete: (conversationId: string) => void;
  onClose: () => void;
}

// Conversation context menu component
const ConversationMenu = ({ 
  conversationId, 
  onDelete, 
  onClose 
}: ConversationMenuProps) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const handleDelete = () => {
    onDelete(conversationId);
    onClose();
  };

  return (
    <div 
      ref={menuRef}
      className="absolute right-0 top-8 z-50 w-48 bg-popover border border-border rounded-md shadow-lg"
    >
      <div className="py-1">
        <button
          onClick={handleDelete}
          className="flex items-center w-full px-3 py-2 text-sm text-destructive hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          <Trash2 className="h-4 w-4 mr-3" />
          Delete conversation
        </button>
      </div>
    </div>
  );
};

// Individual conversation item component
const ConversationItem = ({ 
  conversation, 
  isActive, 
  onSelect, 
  onDelete 
}: ConversationItemProps) => {
  const [showMenu, setShowMenu] = useState(false);

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // Within a week
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const truncateMessage = (message: string, maxLength = 40) => {
    if (message.length <= maxLength) return message;
    return message.substring(0, maxLength) + '...';
  };

  return (
    <div className="relative">
      <button
        onClick={() => onSelect(conversation.conversation_id)}
        className={cn(
          "w-full text-left p-3 rounded-lg transition-colors group",
          isActive 
            ? "bg-primary text-primary-foreground" 
            : "hover:bg-accent hover:text-accent-foreground"
        )}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <MessageCircle className="h-4 w-4 flex-shrink-0" />
              <span className="text-xs text-muted-foreground font-medium">
                {conversation.message_count} message{conversation.message_count !== 1 ? 's' : ''}
              </span>
            </div>
            <p className="text-sm font-medium truncate">
              {truncateMessage(conversation.last_message)}
            </p>
            <div className="flex items-center space-x-2 mt-1">
              <Clock className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">
                {formatDate(conversation.timestamp)}
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className={cn(
              "h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity",
              isActive && "opacity-100 text-primary-foreground hover:bg-primary-foreground/10"
            )}
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(!showMenu);
            }}
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
      </button>

      {showMenu && (
        <ConversationMenu
          conversationId={conversation.conversation_id}
          onDelete={onDelete}
          onClose={() => setShowMenu(false)}
        />
      )}
    </div>
  );
};

// Main Sidebar component
export const Sidebar = ({
  isOpen,
  onToggle,
  activeConversationId,
  onConversationSelect,
  onNewChat,
  onDeleteConversation,
  className,
  userId,
  conversations = [],
  loading = false,
  error = null,
  onRefresh
}: SidebarProps) => {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter conversations based on search query
  const filteredConversations = conversations.filter(conv =>
    conv.last_message.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await onDeleteConversation(conversationId);
      // Refresh conversations if callback provided
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed left-0 top-0 h-full w-80 bg-card border-r border-border z-50 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full",
        className
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h2 className="text-lg font-semibold">Conversations</h2>
            <div className="flex items-center space-x-2">
              <Button
                onClick={onNewChat}
                size="sm"
                className="h-9 w-9 p-0"
                title="New Chat"
              >
                <Plus className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                onClick={onToggle}
                size="sm"
                className="h-9 w-9 p-0 md:hidden"
                title="Close Sidebar"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Search */}
          <div className="p-4 border-b border-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-10 py-2 text-sm bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              />
              {searchQuery && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearSearch}
                  className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 space-y-2">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-sm text-muted-foreground">Loading conversations...</div>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-8 space-y-2">
                  <div className="text-sm text-destructive">Error: {error}</div>
                  {onRefresh && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={onRefresh}
                    >
                      Retry
                    </Button>
                  )}
                </div>
              ) : filteredConversations.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 space-y-3">
                  <MessageCircle className="h-12 w-12 text-muted-foreground opacity-50" />
                  <div className="text-center">
                    <p className="text-sm font-medium">
                      {searchQuery ? 'No conversations found' : 'No conversations yet'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {searchQuery 
                        ? 'Try a different search term' 
                        : 'Start a new chat to begin'
                      }
                    </p>
                  </div>
                  {!searchQuery && (
                    <Button
                      onClick={onNewChat}
                      size="sm"
                      variant="outline"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      New Chat
                    </Button>
                  )}
                </div>
              ) : (
                filteredConversations.map((conversation) => (
                  <ConversationItem
                    key={conversation.conversation_id}
                    conversation={conversation}
                    isActive={activeConversationId === conversation.conversation_id}
                    onSelect={onConversationSelect}
                    onDelete={handleDeleteConversation}
                  />
                ))
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-border p-4">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {filteredConversations.length} conversation{filteredConversations.length !== 1 ? 's' : ''}
              </span>
              {userId && (
                <span>User: {userId}</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

// Default props and exports
Sidebar.displayName = 'Sidebar';

export type { SidebarProps, ConversationItemProps }; 