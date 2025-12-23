import { Header } from "@/components/Header";
import { StatCard } from "@/components/StatCard";
import { SourceCard } from "@/components/SourceCard";
import { ArticleCard } from "@/components/ArticleCard";
import { KeywordCloud } from "@/components/KeywordCloud";
import { CrawlChart } from "@/components/CrawlChart";
import { CategoryPieChart } from "@/components/CategoryPieChart";
import { useRealtimeData, useRealtimeWebSocket } from "@/hooks/useRealtimeData";
import { useDashboardOverview, useSystemStatus } from "@/hooks/useStats";
import {
  Newspaper,
  AlertTriangle,
  Clock,
  Server,
  TrendingUp,
  Wifi,
  WifiOff,
  RefreshCw,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect } from "react";

const Index = () => {
  const queryClient = useQueryClient();
  const { data: realtimeData, isLoading: realtimeLoading, error: realtimeError, refetch } = useRealtimeData();
  const { data: overview } = useDashboardOverview();
  const { data: systemStatus } = useSystemStatus();
  const { isConnected: wsConnected } = useRealtimeWebSocket();

  // Debug log
  useEffect(() => {
    console.log('🔍 Index Page State:', {
      realtimeData,
      realtimeLoading,
      realtimeError,
      overview,
      systemStatus,
      wsConnected
    });
  }, [realtimeData, realtimeLoading, realtimeError, overview, systemStatus, wsConnected]);

  // Use realtime data stats with fallback to dashboard overview
  const stats = realtimeData?.stats || {
    totalArticles: overview?.total_articles || 0,
    totalDisasterArticles: overview?.disaster_articles || 0,
    sources: {},
    severityLevels: { high: 0, medium: 0, low: 0 }
  };
  const disasterArticles = realtimeData?.disasterArticles || [];
  const articles = realtimeData?.articles || [];

  // Calculate sources from realtime data stats
  const NEWS_SOURCES = stats.sources ? Object.entries(stats.sources).map(([domain, count]) => ({
    id: domain.replace('.net', '').replace('.vn', '').replace('https://', '').replace('http://', ''),
    name: domain.includes('vnexpress') ? 'VnExpress' :
          domain.includes('tuoitre') ? 'Tuổi Trẻ' :
          domain.includes('thanhnien') ? 'Thanh Niên' :
          domain.includes('vtv') ? 'VTV' :
          domain.includes('vietnamnet') ? 'VietnamNet' :
          domain.includes('dantri') ? 'Dân Trí' :
          domain.includes('nld') ? 'Người Lao Động' :
          domain.includes('24h') ? '24h' :
          domain.includes('baotintuc') ? 'Báo Tin Tức' :
          domain.includes('nhandan') ? 'Nhân Dân' :
          domain.includes('baomoi') ? 'Báo Mới' : domain,
    domain,
    status: 'active' as const,
    articlesCount: count,
    lastCrawl: new Date().toISOString(),
    categories: ['Thiên tai'],
  })) : [];

  const RECENT_ARTICLES = disasterArticles.slice(0, 10);

  const handleRefresh = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['realtime-data'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
    refetch();
  }, [queryClient, refetch]);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        {/* Connection Status & Refresh */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 text-sm ${wsConnected ? 'text-success' : 'text-muted-foreground'}`}>
              {wsConnected ? (
                <>
                  <Wifi className="h-4 w-4" />
                  <span>Kết nối realtime</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-4 w-4" />
                  <span>Chế độ polling</span>
                </>
              )}
            </div>
            {systemStatus && (
              <div className="text-sm text-muted-foreground">
                API: <span className={systemStatus.status === 'healthy' ? 'text-success' : 'text-warning'}>
                  {systemStatus.status}
                </span>
              </div>
            )}
          </div>
          <button 
            onClick={handleRefresh}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${realtimeLoading ? 'animate-spin' : ''}`} />
            Làm mới
          </button>
        </div>

        {/* Loading/Error States */}
        {realtimeLoading && (
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-primary" />
            <p className="text-muted-foreground">Đang tải dữ liệu từ API...</p>
          </div>
        )}
        {realtimeError && (
          <div className="text-center py-8 bg-destructive/10 rounded-lg">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-destructive" />
            <p className="text-destructive mb-2">Không thể kết nối đến API</p>
            <p className="text-sm text-muted-foreground">
              {realtimeError.message}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Vui lòng kiểm tra API server đang chạy tại http://localhost:8000
            </p>
            <button 
              onClick={handleRefresh}
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Thử lại
            </button>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            title="Tổng bài viết"
            value={stats?.totalArticles.toLocaleString() || '0'}
            subtitle="Trong dữ liệu realtime"
            icon={Newspaper}
            variant="accent"
            trend={{ value: 12, isPositive: true }}
          />
          <StatCard
            title="Bài thiên tai"
            value={stats?.totalDisasterArticles.toLocaleString() || '0'}
            subtitle={`${stats?.totalArticles ? ((stats.totalDisasterArticles / stats.totalArticles) * 100).toFixed(1) : '0'}% tổng số`}
            icon={AlertTriangle}
            variant="danger"
            trend={{ value: 24, isPositive: true }}
          />
          <StatCard
            title="Mức độ nghiêm trọng"
            value={`${stats?.severityLevels?.high || 0} Cao`}
            subtitle={`${stats?.severityLevels?.medium || 0} Trung bình, ${stats?.severityLevels?.low || 0} Thấp`}
            icon={Clock}
            variant="warning"
          />
          <StatCard
            title="Nguồn tin"
            value={`${Object.keys(stats?.sources || {}).length}/8`}
            subtitle="Đang hoạt động"
            icon={Server}
            variant="success"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Chart */}
          <div className="lg:col-span-2">
            <CrawlChart />
          </div>
          
          {/* Pie Chart */}
          <CategoryPieChart />
        </div>

        {/* Sources & Articles */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Sources */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Server className="h-5 w-5 text-accent" />
                Nguồn tin
              </h2>
              <span className="text-sm text-muted-foreground">
                {NEWS_SOURCES.length} nguồn realtime
              </span>
            </div>
            <div className="grid gap-3 max-h-[500px] overflow-y-auto scrollbar-thin pr-2">
              {NEWS_SOURCES.map((source, index) => (
                <SourceCard
                  key={source.id}
                  {...source}
                  status={source.status as "active" | "warning" | "error"}
                  index={index}
                />
              ))}
            </div>
          </div>

          {/* Recent Articles */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Tin mới nhất
              </h2>
              <span className="text-sm text-muted-foreground">
                {RECENT_ARTICLES.length} bài thiên tai
              </span>
            </div>
            <div className="space-y-3 max-h-[500px] overflow-y-auto scrollbar-thin pr-2">
              {RECENT_ARTICLES.map((article, index) => (
                <ArticleCard
                  key={article.url}
                  {...article}
                  severity={article.severity || "medium"}
                  index={index}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Keywords */}
        <KeywordCloud />

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-border/50">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
            <p>
              © 2024 Disaster Monitor. Hệ thống giám sát tin thiên tai Việt Nam.
            </p>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                Dữ liệu realtime: {stats?.totalDisasterArticles || 0} bài thiên tai
              </span>
              <span className="font-mono text-xs">
                v1.0.0
              </span>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Index;
