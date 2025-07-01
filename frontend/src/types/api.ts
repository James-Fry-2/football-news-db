// Base API types matching the FastAPI backend schemas

export interface Article {
  id: number;
  title: string;
  url: string;
  content: string;
  summary?: string;
  published_date: string;
  source: string;
  author?: string;
  status: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface ArticleCreate {
  title: string;
  url: string;
  content: string;
  summary?: string;
  published_date: string;
  source: string;
  author?: string;
  status?: string;
}

export interface ArticleUpdate {
  title?: string;
  content?: string;
  summary?: string;
  published_date?: string;
  source?: string;
  author?: string;
  status?: string;
}

export interface Player {
  id: number;
  name: string;
}

export interface PlayerCreate {
  name: string;
}

export interface PlayerUpdate {
  name?: string;
}

export interface Team {
  id: number;
  name: string;
}

// Search and Vector types
export interface SemanticSearchRequest {
  query: string;
  top_k?: number;
  source_filter?: string;
  sentiment_filter?: 'positive' | 'negative' | 'neutral';
  days_since_published?: number;
}

export interface SearchResult {
  id: string;
  score: number;
  title: string;
  url: string;
  source: string;
  published_date?: string;
  sentiment?: number;
}

export interface ProcessingStats {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
}

// Enhanced Search types
export interface EnhancedSearchRequest {
  query: string;
  top_k?: number;
  ranking_strategy?: 'semantic' | 'hybrid' | 'temporal' | 'engagement';
  filters?: Record<string, any>;
  source_filter?: string;
  date_from?: string;
  date_to?: string;
  sentiment_filter?: 'positive' | 'negative' | 'neutral';
  min_relevance_score?: number;
}

export interface ScoreBreakdown {
  semantic: number;
  temporal?: number;
  source_credibility?: number;
  text_relevance?: number;
  content_quality?: number;
  sentiment?: number;
  total: number;
}

export interface EnhancedSearchResult {
  id: string;
  article_id: number;
  title: string;
  url: string;
  source: string;
  published_date?: string;
  content_snippet: string;
  final_score: number;
  score_breakdown: ScoreBreakdown;
  sentiment_score?: number;
  created_at: string;
  rank: number;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  ranking_strategy: string;
  results: EnhancedSearchResult[];
  search_time_ms: number;
  filters_applied: Record<string, any>;
}

export interface SearchSuggestion {
  suggested_queries: string[];
  related_teams: string[];
  related_players: string[];
}

// Chat types
export interface ChatMessage {
  message: string;
  conversation_id?: string;
  user_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  timestamp: string;
  sources?: any[];
}

export interface ConversationSummary {
  conversation_id: string;
  last_message: string;
  timestamp: string;
  message_count: number;
}

// Analysis types
export interface AnalysisResponse {
  total_articles: number;
  articles_by_source: Record<string, number>;
  articles_by_team: Record<string, number>;
  articles_by_player: Record<string, number>;
}

// Admin types
export interface UserTierRequest {
  user_id: string;
  tier: string;
}

export interface RateLimitStats {
  current_requests: number;
  limit: number;
  window_seconds: number;
  reset_time: number;
}

// Common API response types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  status?: string;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface ArticleFilters extends PaginationParams {
  source?: string;
  team?: string;
  player?: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'message_received' | 'typing' | 'message_complete' | 'error' | 'chunk';
  content?: string;
  conversation_id?: string;
  timestamp?: string;
} 