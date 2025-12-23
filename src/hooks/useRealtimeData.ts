// src/hooks/useRealtimeData.ts
/**
 * Hook for fetching realtime disaster data from the API
 * Includes WebSocket integration for live updates
 */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, useCallback } from 'react';
import { api, API_ENDPOINTS, disasterWebSocket } from '@/lib/api';
import type { 
  ArticlesResponse, 
  Article as APIArticle, 
  RealtimeDisasterEvent,
  RealtimeStats,
  DashboardOverview
} from '@/types/api';

// Legacy Article interface for backward compatibility
export interface Article {
  id: string;
  title: string;
  source: string;
  category: string;
  publishDate: Date;
  summary: string;
  url: string;
  imageUrl: string;
  severity: 'high' | 'medium' | 'low';
  keywords: string[];
  region?: string;
  disaster_type?: string;
}

export interface RealtimeData {
  articles: Article[];
  disasterArticles: Article[];
  stats: {
    totalArticles: number;
    totalDisasterArticles: number;
    sources: { [key: string]: number };
    severityLevels: { [key: string]: number };
  };
}

// Transform API article to legacy format
function transformArticle(article: APIArticle): Article {
  const publishDate = article.publish_date 
    ? new Date(article.publish_date) 
    : article.collected_at 
      ? new Date(article.collected_at)
      : new Date();

  return {
    id: article._id || article.url || Math.random().toString(),
    title: article.title || 'No title',
    source: article.source || 'Unknown',
    category: article.disaster_type || article.category || 'General',
    publishDate: publishDate,
    summary: article.summary || article.text?.substring(0, 200) + '...' || 'No summary',
    url: article.url || '',
    imageUrl: article.top_image || '',
    severity: (article.severity as 'high' | 'medium' | 'low') || 'low',
    keywords: article.keywords || [],
    region: article.region,
    disaster_type: article.disaster_type,
  };
}

// Hook for realtime disaster events via WebSocket
// WebSocket is optional - polling will work without it
export const useRealtimeWebSocket = () => {
  const [events, setEvents] = useState<RealtimeDisasterEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionAttempted, setConnectionAttempted] = useState(false);
  const queryClient = useQueryClient();

  const handleMessage = useCallback((event: RealtimeDisasterEvent) => {
    setEvents(prev => [event, ...prev].slice(0, 100)); // Keep last 100 events
    
    // Invalidate queries to refresh data
    queryClient.invalidateQueries({ queryKey: ['realtime-data'] });
    queryClient.invalidateQueries({ queryKey: ['articles'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
  }, [queryClient]);

  useEffect(() => {
    // Only attempt connection once
    if (connectionAttempted) return;
    setConnectionAttempted(true);

    // Connect to WebSocket (optional - will fallback to polling if fails)
    disasterWebSocket.onMessage(handleMessage);
    
    const connect = async () => {
      try {
        const connected = await disasterWebSocket.connect();
        setIsConnected(connected);
        if (!connected) {
          console.log('ℹ️ WebSocket unavailable, using polling mode');
        }
      } catch (error) {
        console.log('ℹ️ WebSocket connection failed, using polling mode');
        setIsConnected(false);
      }
    };
    
    connect();

    return () => {
      disasterWebSocket.disconnect();
      setIsConnected(false);
    };
  }, [handleMessage, connectionAttempted]);

  return { events, isConnected };
};

// Hook for realtime stats
export const useRealtimeStats = () => {
  return useQuery<RealtimeStats>({
    queryKey: ['realtime-stats'],
    queryFn: async () => {
      return api.get<RealtimeStats>(API_ENDPOINTS.realtimeStats);
    },
    refetchInterval: 15000, // Refetch every 15 seconds
    retry: 2,
  });
};

// Hook for recent disasters
export const useRecentDisasters = (limit = 20) => {
  return useQuery<Article[]>({
    queryKey: ['recent-disasters', limit],
    queryFn: async () => {
      const data = await api.get<ArticlesResponse>(API_ENDPOINTS.realtimeRecent, { limit });
      return (data.articles || []).map(transformArticle);
    },
    refetchInterval: 30000,
    staleTime: 15000,
  });
};

// Main useRealtimeData hook - backward compatible
export const useRealtimeData = () => {
  return useQuery<RealtimeData>({
    queryKey: ['realtime-data'],
    queryFn: async () => {
      try {
        // Fetch dashboard overview for stats
        const overview = await api.get<DashboardOverview>(API_ENDPOINTS.dashboardOverview);
        
        // Fetch recent articles
        const articlesData = await api.get<ArticlesResponse>(API_ENDPOINTS.articles, { 
          limit: 100,
          sort_by: 'collected_at',
          sort_order: 'desc'
        });
        
        const rawArticles = articlesData.articles || [];
        const articles = rawArticles.map(transformArticle);

        // Filter disaster articles (those with disaster_type or high/medium severity)
        const disasterArticles = articles.filter(article => 
          article.disaster_type || 
          article.severity === 'high' || 
          article.severity === 'medium'
        );

        // Calculate source distribution
        const sources: { [key: string]: number } = {};
        articles.forEach(article => {
          sources[article.source] = (sources[article.source] || 0) + 1;
        });

        // Calculate severity distribution
        const severityLevels: { [key: string]: number } = { high: 0, medium: 0, low: 0 };
        disasterArticles.forEach(article => {
          severityLevels[article.severity] = (severityLevels[article.severity] || 0) + 1;
        });

        console.log('✅ Realtime data loaded:', {
          totalArticles: articles.length,
          disasterArticles: disasterArticles.length,
          sources: Object.keys(sources).length
        });

        return {
          articles,
          disasterArticles,
          stats: {
            totalArticles: overview.total_articles || articles.length,
            totalDisasterArticles: overview.disaster_articles || disasterArticles.length,
            sources,
            severityLevels
          }
        };
      } catch (error) {
        console.error('❌ Error fetching realtime data:', error);
        // Return empty data on error
        return {
          articles: [],
          disasterArticles: [],
          stats: {
            totalArticles: 0,
            totalDisasterArticles: 0,
            sources: {},
            severityLevels: { high: 0, medium: 0, low: 0 }
          }
        };
      }
    },
    refetchInterval: 60000, // Refetch every minute
    retry: 3,
    retryDelay: 1000,
    staleTime: 30000,
  });
};