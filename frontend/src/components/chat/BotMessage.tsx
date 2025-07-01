import React, { useState } from 'react';
import { Copy, ExternalLink, RotateCcw, Clock, CheckCircle, AlertCircle, Bot } from 'lucide-react';
import { BotMessageProps } from '@/types/chat';
import { cn } from '@/utils/cn';
import { TypingAnimation } from './TypingAnimation';

export const BotMessage: React.FC<BotMessageProps> = ({
  message,
  showTimestamp = true,
  showSources = true,
  onSourceClick,
  onCopy,
  onRegenerateResponse,
  className,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [copiedToClipboard, setCopiedToClipboard] = useState(false);
  const [expandedSources, setExpandedSources] = useState(false);

  const handleCopy = async () => {
    if (onCopy) {
      onCopy(message.content);
    } else {
      try {
        await navigator.clipboard.writeText(message.content);
        setCopiedToClipboard(true);
        setTimeout(() => setCopiedToClipboard(false), 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    }
  };

  const getStatusIcon = () => {
    switch (message.status) {
      case 'generating':
        return <Clock className="h-3 w-3 animate-spin text-blue-500" />;
      case 'complete':
        return <CheckCircle className="h-3 w-3 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      default:
        return null;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  const renderMarkdown = (content: string) => {
    // Simple markdown rendering for now
    let html = content;
    
    // Convert bold and italic
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert inline code
    html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
    
    // Convert code blocks
    html = html.replace(/```[\s\S]*?```/g, (match) => {
      const code = match.replace(/```(\w+)?\n?/g, '').replace(/```$/, '');
      return `<pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-2"><code class="text-sm font-mono">${code}</code></pre>`;
    });
    
    // Convert line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
  };

  const renderSources = () => {
    if (!message.metadata?.sources || message.metadata.sources.length === 0) {
      return null;
    }

    const sources = message.metadata.sources;
    const visibleSources = expandedSources ? sources : sources.slice(0, 3);

    return (
      <div className="mt-3 p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700">Sources</h4>
          {sources.length > 3 && (
            <button
              onClick={() => setExpandedSources(!expandedSources)}
              className="text-xs text-blue-600 hover:text-blue-700"
            >
              {expandedSources ? 'Show less' : `+${sources.length - 3} more`}
            </button>
          )}
        </div>
        <div className="space-y-2">
          {visibleSources.map((source) => (
            <div
              key={source.id}
              className="flex items-start space-x-3 p-2 bg-white rounded border hover:bg-gray-50 cursor-pointer"
              onClick={() => onSourceClick?.(source)}
            >
              <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {source.title}
                </p>
                <p className="text-xs text-gray-500">
                  {source.source} • {source.published_date && formatTimestamp(source.published_date)}
                  {source.relevance_score && (
                    <span className="ml-2 text-blue-600">
                      {Math.round(source.relevance_score * 100)}% relevant
                    </span>
                  )}
                </p>
                {source.excerpt && (
                  <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                    {source.excerpt}
                  </p>
                )}
              </div>
              <ExternalLink className="h-4 w-4 text-gray-400" />
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderMetadata = () => {
    if (!message.metadata) return null;

    const { confidence, model, tokens, reasoning } = message.metadata;

    return (
      <div className="mt-2 text-xs text-gray-500 space-y-1">
        {confidence && (
          <div>Confidence: {Math.round(confidence * 100)}%</div>
        )}
        {model && tokens && (
          <div>{model} • {tokens} tokens</div>
        )}
        {reasoning && (
          <details className="mt-2">
            <summary className="cursor-pointer text-blue-600 hover:text-blue-700">
              View reasoning
            </summary>
            <p className="mt-1 text-gray-600 text-xs">{reasoning}</p>
          </details>
        )}
      </div>
    );
  };

  return (
    <div
      className={cn("flex mb-4 group", className)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Avatar */}
      <div className="flex-shrink-0 mr-3">
        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
          <Bot className="h-4 w-4 text-gray-600" />
        </div>
      </div>

      {/* Message content */}
      <div className="flex-1 max-w-[80%] space-y-1">
        {/* Message bubble */}
        <div
          className={cn(
            "px-4 py-3 rounded-2xl transition-all duration-200",
            "bg-white border border-gray-200 shadow-sm",
            message.status === 'error' && "border-red-200 bg-red-50",
            message.status === 'generating' && "border-blue-200 bg-blue-50"
          )}
        >
          {message.status === 'generating' && message.isStreaming ? (
            <div className="space-y-2">
              <TypingAnimation isTyping={true} />
              {message.content && (
                <div 
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
                />
              )}
            </div>
          ) : (
            <div 
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
            />
          )}

          {message.status === 'error' && (
            <div className="mt-2 p-2 bg-red-100 border border-red-200 rounded text-sm text-red-700">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4" />
                <span>Failed to generate response</span>
              </div>
            </div>
          )}
        </div>

        {/* Sources */}
        {showSources && renderSources()}

        {/* Metadata */}
        {renderMetadata()}

        {/* Timestamp and status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            {showTimestamp && (
              <span>{formatTimestamp(message.timestamp)}</span>
            )}
            {getStatusIcon()}
          </div>

          {/* Action buttons */}
          {isHovered && (
            <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                className="p-1 rounded hover:bg-gray-100 transition-colors"
                title={copiedToClipboard ? "Copied!" : "Copy message"}
                disabled={copiedToClipboard}
              >
                <Copy className={cn(
                  "h-3 w-3",
                  copiedToClipboard ? "text-green-600" : "text-gray-600"
                )} />
              </button>
              {onRegenerateResponse && message.status !== 'generating' && (
                <button
                  onClick={() => onRegenerateResponse(message.id)}
                  className="p-1 rounded hover:bg-gray-100 transition-colors"
                  title="Regenerate response"
                >
                  <RotateCcw className="h-3 w-3 text-gray-600" />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}; 