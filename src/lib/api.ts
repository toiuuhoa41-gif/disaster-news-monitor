// src/lib/api.ts
/**
 * API Configuration and Client for Disaster Monitor
 * Connects React frontend to FastAPI backend
 */

// API Base URL - Use full URL for direct API access (CORS is enabled on backend)
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  // System
  status: '/api/v1/system/status',
  health: '/api/v1/system/health',
  version: '/api/v1/system/version',
  
  // Articles
  articles: '/api/v1/articles/',
  articleDetail: (id: string) => `/api/v1/articles/${id}`,
  articleSearch: '/api/v1/articles/search',
  
  // Dashboard
  dashboardOverview: '/api/v1/dashboard/overview',
  dashboardHourly: '/api/v1/dashboard/hourly',
  dashboardWeekly: '/api/v1/dashboard/weekly',
  dashboardCategories: '/api/v1/dashboard/categories',
  dashboardRegions: '/api/v1/dashboard/regions',
  dashboardCrawlTimeline: '/api/v1/dashboard/crawl-timeline',
  dashboardDisasterTypes: '/api/v1/dashboard/disaster-types',
  dashboardSeverity: '/api/v1/dashboard/severity',
  
  // Sources
  sources: '/api/v1/sources/',
  sourcesHealth: '/api/v1/sources/health',
  
  // Keywords
  keywords: '/api/v1/keywords/',
  keywordsTop: '/api/v1/keywords/top',
  keywordsTrending: '/api/v1/keywords/trending',
  
  // Regions
  regions: '/api/v1/regions/',
  regionsStats: '/api/v1/regions/stats',
  
  // Realtime
  realtimeStatus: '/api/v1/realtime/status',
  realtimeRecent: '/api/v1/realtime/recent',
  realtimeStats: '/api/v1/realtime/stats',
  
  // WebSocket - use /realtime prefix (without /api/v1)
  wsDisasters: '/realtime/ws/disasters',
  
  // Internal (for testing)
  internalClassify: '/api/v1/internal/classify',
  internalPipelineStats: '/api/v1/internal/pipeline/stats',
};

// HTTP Client with error handling
class APIClient {
  private baseUrl: string;
  
  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }
  
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.detail || `HTTP ${response.status}`,
          response.status,
          errorData
        );
      }
      
      return response.json();
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(
        error instanceof Error ? error.message : 'Network error',
        0
      );
    }
  }
  
  async get<T>(endpoint: string, params?: Record<string, string | number>): Promise<T> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      url = `${endpoint}?${searchParams.toString()}`;
    }
    return this.request<T>(url, { method: 'GET' });
  }
  
  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  
  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

// Custom error class
export class APIError extends Error {
  status: number;
  data: unknown;
  
  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

// Export API client instance
export const api = new APIClient(API_BASE_URL);

// WebSocket connection manager
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3; // Reduced from 5
  private reconnectDelay = 5000; // Increased to 5s
  private listeners: Map<string, Set<(data: unknown) => void>> = new Map();
  private messageCallbacks: Set<(data: unknown) => void> = new Set();
  private shouldReconnect = true;
  
  constructor(endpoint: string) {
    this.url = `${WS_BASE_URL}${endpoint}`;
  }
  
  connect(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve(true);
        return;
      }
      
      try {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          console.log('✅ WebSocket connected to:', this.url);
          this.reconnectAttempts = 0;
          this.shouldReconnect = true;
          this.emit('connected', { timestamp: new Date().toISOString() });
          resolve(true);
        };
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.emit(data.type || 'message', data);
            // Call all message callbacks
            this.messageCallbacks.forEach(callback => callback(data));
          } catch (error) {
            console.error('WebSocket message parse error:', error);
          }
        };
        
        this.ws.onclose = (event) => {
          // Don't reconnect on 403 Forbidden or other auth errors
          if (event.code === 1008 || event.code === 403) {
            console.log('⚠️ WebSocket closed with auth error, not reconnecting');
            this.shouldReconnect = false;
          } else {
            console.log('⚠️ WebSocket disconnected');
          }
          this.emit('disconnected', {});
          if (this.shouldReconnect) {
            this.attemptReconnect();
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.emit('error', { error });
          // Stop reconnecting on errors (likely CORS or server issue)
          this.shouldReconnect = false;
          resolve(false);
        };
        
        // Timeout for connection
        setTimeout(() => {
          if (this.ws?.readyState !== WebSocket.OPEN) {
            this.shouldReconnect = false;
            resolve(false);
          }
        }, 5000);
      } catch (error) {
        console.error('❌ WebSocket connection failed:', error);
        this.shouldReconnect = false;
        resolve(false);
      }
    });
  }
  
  private attemptReconnect(): void {
    if (!this.shouldReconnect) return;
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Reconnecting... attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      setTimeout(() => this.connect(), this.reconnectDelay);
    } else {
      console.log('ℹ️ Max reconnection attempts reached, using polling mode');
      this.shouldReconnect = false;
    }
  }
  
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageCallbacks.clear();
  }
  
  // Register a callback for all incoming messages
  onMessage(callback: (data: unknown) => void): void {
    this.messageCallbacks.add(callback);
  }
  
  // Unregister a message callback
  offMessage(callback: (data: unknown) => void): void {
    this.messageCallbacks.delete(callback);
  }
  
  on(event: string, callback: (data: unknown) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }
  
  off(event: string, callback: (data: unknown) => void): void {
    this.listeners.get(event)?.delete(callback);
  }
  
  private emit(event: string, data: unknown): void {
    this.listeners.get(event)?.forEach(callback => callback(data));
  }
  
  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message');
    }
  }
  
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Export WebSocket instance for disaster feed
export const disasterWebSocket = new WebSocketManager(API_ENDPOINTS.wsDisasters);

// Helper function to check API health
export async function checkAPIHealth(): Promise<boolean> {
  try {
    await api.get(API_ENDPOINTS.health);
    return true;
  } catch {
    return false;
  }
}

// Helper function to get system status
export async function getSystemStatus() {
  return api.get(API_ENDPOINTS.status);
}