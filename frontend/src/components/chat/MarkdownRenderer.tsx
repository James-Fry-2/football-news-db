import React from 'react';
import { MarkdownOptions } from '@/types/chat';
import { cn } from '@/utils/cn';

interface MarkdownRendererProps {
  content: string;
  options?: MarkdownOptions;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  options = {},
  className,
}) => {
  const {
    enableBreaks = true,
  } = options;

  // For now, we'll render a simplified version without external dependencies
  // This can be enhanced later with react-markdown and plugins
  const renderContent = () => {
    // Basic markdown parsing for demonstration
    let html = content;
    
    // Convert markdown headers
    html = html.replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold mb-2">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold mb-3">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mb-4">$1</h1>');
    
    // Convert bold and italic
    html = html.replace(/\*\*(.*)\*\*/gim, '<strong class="font-semibold">$1</strong>');
    html = html.replace(/\*(.*)\*/gim, '<em class="italic">$1</em>');
    
    // Convert inline code
    html = html.replace(/`([^`]+)`/gim, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
    
    // Convert code blocks
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/gim, (_match, _language, code) => {
      return `<pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code class="text-sm font-mono">${code.trim()}</code></pre>`;
    });
    
    // Convert links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" class="text-blue-600 hover:text-blue-700 underline" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Convert line breaks if enabled
    if (enableBreaks) {
      html = html.replace(/\n/gim, '<br>');
    }
    
    // Convert lists
    html = html.replace(/^\* (.+)$/gim, '<li class="list-disc ml-4">$1</li>');
    html = html.replace(/^- (.+)$/gim, '<li class="list-disc ml-4">$1</li>');
    
    // Convert numbered lists
    html = html.replace(/^\d+\. (.+)$/gim, '<li class="list-decimal ml-4">$1</li>');
    
    return html;
  };

  return (
    <div 
      className={cn(
        "prose prose-sm max-w-none",
        "prose-headings:text-gray-900 prose-p:text-gray-700",
        "prose-code:text-gray-800 prose-pre:bg-gray-900",
        "prose-a:text-blue-600 prose-strong:text-gray-900",
        className
      )}
      dangerouslySetInnerHTML={{ __html: renderContent() }}
    />
  );
};

// Enhanced version that would use react-markdown (commented out for now)
/*
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeKatex from 'rehype-katex';

export const MarkdownRendererEnhanced: React.FC<MarkdownRendererProps> = ({
  content,
  options = {},
  className,
}) => {
  const {
    enableSyntaxHighlighting = true,
    enableMath = false,
    enableTables = true,
    enableBreaks = true,
  } = options;

  const remarkPlugins = [
    enableTables && remarkGfm,
    enableMath && remarkMath,
  ].filter(Boolean);

  const rehypePlugins = [
    enableSyntaxHighlighting && rehypeHighlight,
    enableMath && rehypeKatex,
  ].filter(Boolean);

  return (
    <ReactMarkdown
      className={cn(
        "prose prose-sm max-w-none",
        "prose-headings:text-gray-900 prose-p:text-gray-700",
        "prose-code:text-gray-800 prose-pre:bg-gray-900",
        "prose-a:text-blue-600 prose-strong:text-gray-900",
        className
      )}
      remarkPlugins={remarkPlugins}
      rehypePlugins={rehypePlugins}
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
              <code className={className} {...props}>
                {children}
              </code>
            </pre>
          ) : (
            <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props}>
              {children}
            </code>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
};
*/ 