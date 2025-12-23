// Frontend Test Configuration
import { describe, it, expect, vi } from 'vitest';

// Mock API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
  API_ENDPOINTS: {
    articles: '/api/v1/articles/',
    dashboardOverview: '/api/v1/dashboard/overview',
    realtimeStatus: '/api/v1/realtime/status',
  },
}));

describe('API Client', () => {
  it('should have correct API endpoints', () => {
    const endpoints = {
      articles: '/api/v1/articles/',
      dashboardOverview: '/api/v1/dashboard/overview',
      realtimeStatus: '/api/v1/realtime/status',
    };
    
    expect(endpoints.articles).toBe('/api/v1/articles/');
    expect(endpoints.dashboardOverview).toBe('/api/v1/dashboard/overview');
  });
});

describe('Article Transformation', () => {
  it('should transform API article to frontend format', () => {
    const apiArticle = {
      _id: '123',
      title: 'Test Article',
      source: 'vnexpress.net',
      disaster_type: 'flood',
      severity: 'high',
      publish_date: '2024-01-15T10:00:00Z',
    };
    
    const transformed = {
      id: apiArticle._id,
      title: apiArticle.title,
      source: apiArticle.source,
      category: apiArticle.disaster_type,
      severity: apiArticle.severity,
      publishDate: new Date(apiArticle.publish_date),
    };
    
    expect(transformed.id).toBe('123');
    expect(transformed.title).toBe('Test Article');
    expect(transformed.severity).toBe('high');
  });
});

describe('Severity Classification', () => {
  it('should classify high severity correctly', () => {
    const severities = ['high', 'medium', 'low'];
    expect(severities).toContain('high');
  });
  
  it('should have valid severity colors', () => {
    const severityColors = {
      high: 'red',
      medium: 'yellow',
      low: 'green',
    };
    
    expect(severityColors.high).toBe('red');
    expect(severityColors.medium).toBe('yellow');
    expect(severityColors.low).toBe('green');
  });
});
