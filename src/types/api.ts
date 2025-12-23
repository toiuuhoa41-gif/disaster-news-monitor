// src/types/api.ts
/**
 * API Response Types for Disaster Monitor
 * Synced with FastAPI backend schemas
 */

// =====================================================
// Article Types
// =====================================================

export interface Article {
  id?: string;
  url: string;
  source: string;
  category?: string;
  title: string;
  authors?: string[];
  publish_date?: string;
  published_at?: string;
  update_date?: string;
  processed_at?: string;
  tags?: string[];
  text?: string;
  content?: string;
  summary?: string;
  keywords?: string[];
  media?: {
    top_image?: string;
    images?: string[];
    videos?: string[];
  };
  language?: string;
  
  // Classification fields
  is_disaster?: boolean;
  disaster_type?: string;
  severity?: 'high' | 'medium' | 'low' | 'none';
  confidence?: number;
  region?: string;
  matched_keywords?: string[];
  
  // Metadata
  reliability_score?: number;
  is_google_news?: boolean;
  original_source?: string;
}

export interface ArticlesResponse {
  articles: Article[];
  total?: number;
  page?: number;
  limit?: number;
}

export interface ArticleSearchParams {
  q?: string;
  source?: string;
  severity?: string;
  disaster_type?: string;
  region?: string;
  limit?: number;
  offset?: number;
  start_date?: string;
  end_date?: string;
}

// =====================================================
// Dashboard/Stats Types
// =====================================================

export interface DashboardOverview {
  total_articles: number;
  disaster_articles: number;
  disaster_ratio: number;
  today_articles: number;
  active_sources: number;
  severity_high: number;
  severity_medium: number;
  severity_low: number;
  // Optional fields for backward compatibility
  by_severity?: {
    high: number;
    medium: number;
    low: number;
  };
  by_type?: Record<string, number>;
  by_region?: Record<string, number>;
  last_updated?: string;
}

export interface HourlyStats {
  hour: string;
  count: number;
  articles: number;
  disaster_count: number;
  disaster_articles: number;
}

export interface WeeklyStats {
  date: string;
  count: number;
  disaster_count: number;
}

export interface CategoryStats {
  category: string;
  count: number;
  percentage: number;
}

export interface RegionStats {
  region: string;
  count: number;
  severity_breakdown: {
    high: number;
    medium: number;
    low: number;
  };
}

// =====================================================
// Source Types
// =====================================================

export interface NewsSource {
  id?: string;
  name: string;
  domain: string;
  type: 'news' | 'government' | 'aggregator' | 'local';
  country: string;
  language: string;
  reliability_score: number;
  has_native_rss: boolean;
  rss_feeds: string[];
  google_news_rss?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SourceHealth {
  source_id: string;
  domain: string;
  rss_status: 'healthy' | 'warning' | 'error' | 'unknown';
  has_native_rss: boolean;
  reliability_score: number;
  status: 'healthy' | 'warning' | 'error';
}

export interface SourcesHealthSummary {
  total_sources: number;
  active_sources: number;
  with_native_rss: number;
  with_google_rss: number;
  status: string;
  checked_at: string;
}

// =====================================================
// Keyword Types
// =====================================================

export interface Keyword {
  keyword: string;
  count: number;
  category?: string;
  trend?: 'up' | 'down' | 'stable';
}

export interface TopKeywords {
  keywords: Keyword[];
  period: string;
}

// =====================================================
// System Types
// =====================================================

export interface SystemStatus {
  system_status: string;
  realtime_ingestion: boolean;
  active_sources: number;
  total_sources: number;
  version: string;
  server_time: string;
}

export interface SystemHealth {
  status: string;
  database: string;
  crawler: string;
  websocket: string;
  uptime: number;
}

// =====================================================
// Realtime Types
// =====================================================

export interface RealtimeStatus {
  status: string;
  active_connections: number;
  timestamp: string;
}

export interface RealtimeStats {
  timestamp: string;
  today_disasters: number;
  by_severity: {
    high: number;
    medium: number;
    low: number;
  };
  by_type: Record<string, number>;
  active_connections: number;
}

export interface RealtimeDisasterEvent {
  type: 'new_disaster' | 'heartbeat' | 'connected';
  data?: {
    title: string;
    source: string;
    url: string;
    disaster_type: string;
    severity: string;
    region?: string;
    confidence: number;
    matched_keywords: string[];
    published_at?: string;
    processed_at: string;
  };
  timestamp?: string;
  message?: string;
}

// =====================================================
// Pipeline Types
// =====================================================

export interface PipelineStats {
  total_processed: number;
  disaster_articles: number;
  non_disaster_articles: number;
  failed_articles: number;
  avg_confidence: number;
  processing_time_ms: number;
}

export interface ClassificationResult {
  is_disaster: boolean;
  disaster_type: string;
  severity: string;
  confidence: number;
  region?: string;
  matched_keywords: string[];
  details?: {
    deaths: number;
    missing: number;
    injured: number;
    houses_affected: number;
    severity_keywords: string[];
  };
}

// =====================================================
// Chart Data Types (for frontend)
// =====================================================

export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

export interface TimeSeriesDataPoint {
  time: string;
  value: number;
  label?: string;
}

// =====================================================
// Dashboard Chart Types
// =====================================================

export interface CrawlTimelineItem {
  hour: string;
  articles: number;
  disaster_articles: number;
}

export interface DisasterTypeDistribution {
  weather: number;
  flood: number;
  drought: number;
  earthquake: number;
  fire: number;
  general: number;
  other: number;
}

export interface SeverityBreakdown {
  high: number;
  medium: number;
  low: number;
  none: number;
  total: number;
}
