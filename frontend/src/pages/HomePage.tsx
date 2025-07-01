import React from 'react';

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">
          Football News Database
        </h1>
        <p className="text-lg text-muted-foreground mt-2">
          Intelligent football news aggregation with semantic search and AI-powered chat
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-2">Latest Articles</h3>
          <p className="text-muted-foreground">Browse the latest football news from multiple sources</p>
        </div>
        
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-2">Semantic Search</h3>
          <p className="text-muted-foreground">Find articles using advanced AI-powered search</p>
        </div>
        
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-2">AI Chat</h3>
          <p className="text-muted-foreground">Ask questions about football news and get intelligent responses</p>
        </div>
      </div>
    </div>
  );
}; 