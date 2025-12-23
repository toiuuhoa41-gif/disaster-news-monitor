import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useDashboardOverview } from "@/hooks/useStats";
import { RefreshCw } from "lucide-react";

// Colors for severity levels
const SEVERITY_COLORS = {
  high: "hsl(0, 84%, 60%)",      // Red
  medium: "hsl(35, 85%, 55%)",   // Orange  
  low: "hsl(188, 85%, 50%)",     // Cyan
};

export function CrawlChart() {
  const { data: overview, isLoading, error } = useDashboardOverview();

  // Transform overview data to severity chart format
  const chartData = overview ? [
    { name: "Cao", value: overview.severity_high || 0, color: SEVERITY_COLORS.high },
    { name: "Trung bình", value: overview.severity_medium || 0, color: SEVERITY_COLORS.medium },
    { name: "Thấp", value: overview.severity_low || 0, color: SEVERITY_COLORS.low },
  ] : [];

  const totalDisaster = overview?.disaster_articles || 0;

  if (isLoading) {
    return (
      <div className="glass rounded-xl p-5 animate-fade-in" style={{ animationDelay: "150ms" }}>
        <h3 className="text-lg font-semibold mb-4">Phân bố mức độ nghiêm trọng</h3>
        <div className="h-64 flex items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass rounded-xl p-5 animate-fade-in" style={{ animationDelay: "150ms" }}>
        <h3 className="text-lg font-semibold mb-4">Phân bố mức độ nghiêm trọng</h3>
        <div className="h-64 flex items-center justify-center text-muted-foreground">
          Không thể tải dữ liệu
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl p-5 animate-fade-in" style={{ animationDelay: "150ms" }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Phân bố mức độ nghiêm trọng</h3>
        <span className="text-sm text-muted-foreground">{totalDisaster} bài thiên tai</span>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 30 }}>
            <XAxis 
              type="number" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
            />
            <YAxis 
              type="category" 
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(215 20% 55%)", fontSize: 12 }}
              width={80}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(222 47% 10%)",
                border: "1px solid hsl(217 33% 17%)",
                borderRadius: "8px",
                boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
              }}
              labelStyle={{ color: "hsl(210 40% 96%)" }}
              itemStyle={{ color: "hsl(210 40% 96%)" }}
              formatter={(value: number) => [`${value} bài`, "Số lượng"]}
            />
            <Bar 
              dataKey="value" 
              radius={[0, 4, 4, 0]}
              barSize={32}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-center gap-6 mt-4">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: item.color }}
            />
            <span className="text-sm text-muted-foreground">{item.name}: {item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
