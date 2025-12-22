import { Header } from "@/components/Header";
import { StatCard } from "@/components/StatCard";
import { SourceCard } from "@/components/SourceCard";
import { ArticleCard } from "@/components/ArticleCard";
import { KeywordCloud } from "@/components/KeywordCloud";
import { CrawlChart } from "@/components/CrawlChart";
import { CategoryPieChart } from "@/components/CategoryPieChart";
import { NEWS_SOURCES, RECENT_ARTICLES, CRAWL_STATS } from "@/data/mockData";
import {
  Newspaper,
  AlertTriangle,
  Clock,
  Server,
  TrendingUp,
} from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            title="Tổng bài viết"
            value={CRAWL_STATS.totalArticles.toLocaleString()}
            subtitle="Trong 30 ngày qua"
            icon={Newspaper}
            variant="accent"
            trend={{ value: 12, isPositive: true }}
          />
          <StatCard
            title="Bài thiên tai"
            value={CRAWL_STATS.disasterArticles.toLocaleString()}
            subtitle={`${((CRAWL_STATS.disasterArticles / CRAWL_STATS.totalArticles) * 100).toFixed(1)}% tổng số`}
            icon={AlertTriangle}
            variant="danger"
            trend={{ value: 24, isPositive: true }}
          />
          <StatCard
            title="Hôm nay"
            value={CRAWL_STATS.todayArticles}
            subtitle="Bài đã crawl"
            icon={Clock}
            variant="default"
          />
          <StatCard
            title="Nguồn tin"
            value={`${CRAWL_STATS.activeSources}/8`}
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
                {NEWS_SOURCES.length} nguồn
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
                {RECENT_ARTICLES.length} bài
              </span>
            </div>
            <div className="space-y-3 max-h-[500px] overflow-y-auto scrollbar-thin pr-2">
              {RECENT_ARTICLES.map((article, index) => (
                <ArticleCard
                  key={article.id}
                  {...article}
                  severity={article.severity as "high" | "medium" | "low"}
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
                Hệ thống hoạt động bình thường
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
