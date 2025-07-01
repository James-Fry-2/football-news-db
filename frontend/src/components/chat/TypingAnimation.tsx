import React from 'react';
import { TypingAnimationProps } from '@/types/chat';
import { cn } from '@/utils/cn';

export const TypingAnimation: React.FC<TypingAnimationProps> = ({
  isTyping,
  duration = 1500,
  className,
}) => {
  if (!isTyping) return null;
  

  return (
    <div className={cn("flex items-center space-x-1", className)}>
      <div className="flex space-x-1">
        <div
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{
            animationDuration: `${duration}ms`,
            animationDelay: '0ms',
          }}
        />
        <div
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{
            animationDuration: `${duration}ms`,
            animationDelay: '150ms',
          }}
        />
        <div
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{
            animationDuration: `${duration}ms`,
            animationDelay: '300ms',
          }}
        />
      </div>
      <span className="text-sm text-gray-500 ml-2">Assistant is typing...</span>
    </div>
  );
}; 