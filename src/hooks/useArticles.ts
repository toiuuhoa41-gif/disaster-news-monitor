// src/hooks/useArticles.ts
/**
 * Hook for fetching articles from the API
 */
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { api, API_ENDPOINTS } from '@/lib/api';
import type { Article, ArticlesResponse, ArticleSearchParams } from '@/types/api';

// Re-export Article type for backward compatibility
export type { Article };

export interface UseArticlesOptions {
  limit?: number;
  offset?: number;
  source?: string;
  severity?: string;
  disaster_type?: string;
  region?: string;
  is_disaster?: boolean;
}

export const useArticles = (options: UseArticlesOptions = {}) => {
  const { limit = 50, offset = 0, source, severity, disaster_type, region, is_disaster } = options;
  
  return useQuery<ArticlesResponse>({
    queryKey: ['articles', limit, offset, source, severity, disaster_type, region, is_disaster],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        limit,
        offset,
      };
      
      if (source) params.source = source;
      if (severity) params.severity = severity;
      if (disaster_type) params.disaster_type = disaster_type;
      if (region) params.region = region;
      if (is_disaster !== undefined) params.is_disaster = is_disaster ? 'true' : 'false';
      
      return api.get<ArticlesResponse>(API_ENDPOINTS.articles, params);
    },
    refetchInterval: 60000, // Refetch every minute
    retry: 3,
    retryDelay: 1000,
    staleTime: 30000,
  });
};

export const useArticleSearch = (searchParams: ArticleSearchParams) => {
  return useQuery<ArticlesResponse>({
    queryKey: ['articles-search', searchParams],
    queryFn: async () => {
      const params: Record<string, string | number> = {};
      
      if (searchParams.q) params.q = searchParams.q;
      if (searchParams.source) params.source = searchParams.source;
      if (searchParams.severity) params.severity = searchParams.severity;
      if (searchParams.disaster_type) params.disaster_type = searchParams.disaster_type;
      if (searchParams.region) params.region = searchParams.region;
      if (searchParams.limit) params.limit = searchParams.limit;
      if (searchParams.offset) params.offset = searchParams.offset;
      if (searchParams.start_date) params.start_date = searchParams.start_date;
      if (searchParams.end_date) params.end_date = searchParams.end_date;
      
      return api.get<ArticlesResponse>(API_ENDPOINTS.articleSearch, params);
    },
    enabled: !!searchParams.q || !!searchParams.source || !!searchParams.severity,
    retry: 2,
  });
};

export const useArticleDetail = (id: string) => {
  return useQuery<Article>({
    queryKey: ['article', id],
    queryFn: async () => {
      return api.get<Article>(API_ENDPOINTS.articleDetail(id));
    },
    enabled: !!id,
  });
};

export const useDisasterArticles = (limit = 50) => {
  return useQuery<ArticlesResponse>({
    queryKey: ['disaster-articles', limit],
    queryFn: async () => {
      return api.get<ArticlesResponse>(API_ENDPOINTS.articles, {
        limit,
        is_disaster: 'true',
      });
    },
    refetchInterval: 30000, // Refetch every 30 seconds for disaster articles
    retry: 3,
  });
};

// Infinite scroll hook for articles
export const useInfiniteArticles = (options: Omit<UseArticlesOptions, 'offset'> = {}) => {
  const { limit = 20, source, severity, disaster_type, region, is_disaster } = options;
  
  return useInfiniteQuery<ArticlesResponse>({
    queryKey: ['infinite-articles', limit, source, severity, disaster_type, region, is_disaster],
    queryFn: async ({ pageParam = 0 }) => {
      const params: Record<string, string | number> = {
        limit,
        offset: pageParam as number,
      };
      
      if (source) params.source = source;
      if (severity) params.severity = severity;
      if (disaster_type) params.disaster_type = disaster_type;
      if (region) params.region = region;
      if (is_disaster !== undefined) params.is_disaster = is_disaster ? 'true' : 'false';
      
      return api.get<ArticlesResponse>(API_ENDPOINTS.articles, params);
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      const totalFetched = allPages.reduce((acc, page) => acc + page.articles.length, 0);
      if (lastPage.articles.length < limit) {
        return undefined; // No more pages
      }
      return totalFetched;
    },
  });
};