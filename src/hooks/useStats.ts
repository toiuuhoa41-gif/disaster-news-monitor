// src/hooks/useStats.ts
/**
 * Hooks for fetching dashboard statistics from the API
 */
import { useQuery } from '@tanstack/react-query';
import { api, API_ENDPOINTS } from '@/lib/api';
import type { 
  DashboardOverview, 
  HourlyStats, 
  WeeklyStats, 
  CategoryStats,
  RegionStats,
  SystemStatus,
  SourcesHealthSummary,
  RealtimeStats,
  CrawlTimelineItem,
  DisasterTypeDistribution,
  SeverityBreakdown
} from '@/types/api';

// Legacy interface for backward compatibility
export interface StatsData {
  totalArticles: number;
  disasterArticles: number;
  todayArticles: number;
  activeSources: number;
}

// Dashboard Overview Hook
export const useDashboardOverview = () => {
  return useQuery<DashboardOverview>({
    queryKey: ['dashboard-overview'],
    queryFn: async () => {
      return api.get<DashboardOverview>(API_ENDPOINTS.dashboardOverview);
    },
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
    retryDelay: 1000,
    staleTime: 15000,
  });
};

// Hourly Stats Hook
export const useHourlyStats = (hours = 24) => {
  return useQuery<HourlyStats[]>({
    queryKey: ['hourly-stats', hours],
    queryFn: async () => {
      return api.get<HourlyStats[]>(API_ENDPOINTS.dashboardHourly, { hours });
    },
    refetchInterval: 60000,
    staleTime: 30000,
  });
};

// Weekly Stats Hook
export const useWeeklyStats = (days = 7) => {
  return useQuery<WeeklyStats[]>({
    queryKey: ['weekly-stats', days],
    queryFn: async () => {
      return api.get<WeeklyStats[]>(API_ENDPOINTS.dashboardWeekly, { days });
    },
    refetchInterval: 300000, // Refetch every 5 minutes
    staleTime: 60000,
  });
};

// Category Stats Hook
export const useCategoryStats = () => {
  return useQuery<CategoryStats[]>({
    queryKey: ['category-stats'],
    queryFn: async () => {
      return api.get<CategoryStats[]>(API_ENDPOINTS.dashboardCategories);
    },
    refetchInterval: 60000,
    staleTime: 30000,
  });
};

// Region Stats Hook
export const useRegionStats = () => {
  return useQuery<RegionStats[]>({
    queryKey: ['region-stats'],
    queryFn: async () => {
      return api.get<RegionStats[]>(API_ENDPOINTS.regionsStats);
    },
    refetchInterval: 60000,
    staleTime: 30000,
  });
};

// System Status Hook
export const useSystemStatus = () => {
  return useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: async () => {
      return api.get<SystemStatus>(API_ENDPOINTS.status);
    },
    refetchInterval: 10000, // Check every 10 seconds
    retry: 2,
  });
};

// Sources Health Hook
export const useSourcesHealth = () => {
  return useQuery<SourcesHealthSummary>({
    queryKey: ['sources-health'],
    queryFn: async () => {
      return api.get<SourcesHealthSummary>(API_ENDPOINTS.sourcesHealth);
    },
    refetchInterval: 60000,
    staleTime: 30000,
  });
};

// Realtime Stats Hook
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

// Legacy useStats hook for backward compatibility
export const useStats = () => {
  return useQuery<StatsData>({
    queryKey: ['stats-legacy'],
    queryFn: async () => {
      try {
        // Try to get data from dashboard overview
        const overview = await api.get<DashboardOverview>(API_ENDPOINTS.dashboardOverview);
        return {
          totalArticles: overview.total_articles || 0,
          disasterArticles: overview.disaster_articles || 0,
          todayArticles: overview.today_articles || 0,
          activeSources: overview.active_sources || 0,
        };
      } catch {
        // Fallback to system status
        const status = await api.get<SystemStatus>(API_ENDPOINTS.status);
        return {
          totalArticles: 0,
          disasterArticles: 0,
          todayArticles: 0,
          activeSources: status.active_sources || 0,
        };
      }
    },
    refetchInterval: 30000,
    retry: 3,
    retryDelay: 1000,
  });
};

// Crawl Timeline Hook - for hourly activity chart
export const useCrawlTimeline = () => {
  return useQuery<CrawlTimelineItem[]>({
    queryKey: ['crawl-timeline'],
    queryFn: async () => {
      return api.get<CrawlTimelineItem[]>(API_ENDPOINTS.dashboardCrawlTimeline);
    },
    refetchInterval: 120000, // Refetch every 2 minutes
    staleTime: 60000,
  });
};

// Disaster Type Distribution Hook - for pie chart
export const useDisasterTypeDistribution = () => {
  return useQuery<DisasterTypeDistribution>({
    queryKey: ['disaster-type-distribution'],
    queryFn: async () => {
      return api.get<DisasterTypeDistribution>(API_ENDPOINTS.dashboardDisasterTypes);
    },
    refetchInterval: 120000,
    staleTime: 60000,
  });
};

// Severity Breakdown Hook
export const useSeverityBreakdown = () => {
  return useQuery<SeverityBreakdown>({
    queryKey: ['severity-breakdown'],
    queryFn: async () => {
      return api.get<SeverityBreakdown>(API_ENDPOINTS.dashboardSeverity);
    },
    refetchInterval: 60000,
    staleTime: 30000,
  });
};