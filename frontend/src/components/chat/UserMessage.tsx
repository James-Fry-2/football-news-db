import React, { useState } from 'react';
import { Clock, Check, AlertCircle, RotateCcw, Edit2, Trash2 } from 'lucide-react';
import { UserMessageProps } from '@/types/chat';
import { cn } from '@/utils/cn';

export const UserMessage: React.FC<UserMessageProps> = ({
  message,
  showTimestamp = true,
  showStatus = true,
  onRetry,
  onEdit,
  onDelete,
  className,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const [isHovered, setIsHovered] = useState(false);

  const handleEdit = () => {
    if (isEditing) {
      if (editContent.trim() !== message.content && onEdit) {
        onEdit(message.id, editContent.trim());
      }
      setIsEditing(false);
    } else {
      setIsEditing(true);
    }
  };

  const handleCancel = () => {
    setEditContent(message.content);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleEdit();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const getStatusIcon = () => {
    switch (message.status) {
      case 'sending':
        return <Clock className="h-3 w-3 animate-spin text-blue-500" />;
      case 'sent':
        return <Check className="h-3 w-3 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      default:
        return null;
    }
  };

  const formatTimestamp = (timestamp: string) => {
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
    
    // More than 24 hours ago
    return date.toLocaleDateString();
  };

  return (
    <div 
      className={cn(
        "flex justify-end mb-4 group",
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex flex-col items-end max-w-[80%] space-y-1">
        {/* Message bubble */}
        <div
          className={cn(
            "px-4 py-2 rounded-2xl transition-all duration-200",
            "bg-blue-600 text-white shadow-sm",
            message.status === 'failed' && "bg-red-500",
            message.status === 'sending' && "opacity-70",
            isEditing && "ring-2 ring-blue-400"
          )}
        >
          {isEditing ? (
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full bg-transparent border-none outline-none resize-none text-white placeholder-blue-200"
              placeholder="Type your message..."
              rows={Math.max(1, editContent.split('\n').length)}
              autoFocus
            />
          ) : (
            <div className="whitespace-pre-wrap break-words">
              {message.content}
              {message.edited && (
                <span className="text-xs text-blue-200 ml-2">(edited)</span>
              )}
            </div>
          )}
        </div>

        {/* Timestamp and status */}
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          {showTimestamp && (
            <span>{formatTimestamp(message.timestamp)}</span>
          )}
          {showStatus && getStatusIcon()}
        </div>

        {/* Action buttons */}
        {(isHovered || isEditing) && (
          <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {isEditing ? (
              <>
                <button
                  onClick={handleEdit}
                  className="p-1 rounded hover:bg-gray-100 transition-colors"
                  title="Save changes"
                >
                  <Check className="h-3 w-3 text-green-600" />
                </button>
                <button
                  onClick={handleCancel}
                  className="p-1 rounded hover:bg-gray-100 transition-colors"
                  title="Cancel"
                >
                  <AlertCircle className="h-3 w-3 text-gray-600" />
                </button>
              </>
            ) : (
              <>
                {message.status === 'failed' && onRetry && (
                  <button
                    onClick={() => onRetry(message.id)}
                    className="p-1 rounded hover:bg-gray-100 transition-colors"
                    title="Retry sending"
                  >
                    <RotateCcw className="h-3 w-3 text-blue-600" />
                  </button>
                )}
                {onEdit && message.status !== 'sending' && (
                  <button
                    onClick={handleEdit}
                    className="p-1 rounded hover:bg-gray-100 transition-colors"
                    title="Edit message"
                  >
                    <Edit2 className="h-3 w-3 text-gray-600" />
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={() => onDelete(message.id)}
                    className="p-1 rounded hover:bg-gray-100 transition-colors"
                    title="Delete message"
                  >
                    <Trash2 className="h-3 w-3 text-red-600" />
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}; 