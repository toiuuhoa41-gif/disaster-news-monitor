import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { HOURLY_STATS } from "@/data/mockData";

export function CrawlChart() {
  return (
    <div className="glass rounded-xl p-5 animate-fade-in" style={{ animationDelay: "150ms" }}>
      <h3 className="text-lg font-semibold mb-4">Hoạt động crawl hôm nay</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={HOURLY_STATS}>
            <defs>
              <linearGradient id="colorArticles" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(188 85% 50%)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(188 85% 50%)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorDisaster" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(0 84% 60%)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(0 84% 60%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="hour"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
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
            />
            <Area
              type="monotone"
              dataKey="articles"
              stroke="hsl(188 85% 50%)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorArticles)"
              name="Tổng bài"
            />
            <Area
              type="monotone"
              dataKey="disaster"
              stroke="hsl(0 84% 60%)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorDisaster)"
              name="Thiên tai"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-center gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-accent" />
          <span className="text-sm text-muted-foreground">Tổng bài viết</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-primary" />
          <span className="text-sm text-muted-foreground">Bài thiên tai</span>
        </div>
      </div>
    </div>
  );
}
