import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { useDisasterTypeDistribution } from "@/hooks/useStats";
import { RefreshCw } from "lucide-react";

// Map disaster types to Vietnamese names and colors
const DISASTER_TYPE_CONFIG: Record<string, { name: string; color: string }> = {
  weather: { name: "Thời tiết", color: "hsl(var(--chart-1))" },
  flood: { name: "Lũ lụt", color: "hsl(var(--chart-2))" },
  drought: { name: "Hạn hán", color: "hsl(var(--chart-3))" },
  earthquake: { name: "Động đất", color: "hsl(var(--chart-4))" },
  fire: { name: "Cháy", color: "hsl(35, 85%, 55%)" },
  general: { name: "Chung", color: "hsl(var(--chart-5))" },
  other: { name: "Khác", color: "hsl(215, 20%, 55%)" },
};

export function CategoryPieChart() {
  const { data: distribution, isLoading, error } = useDisasterTypeDistribution();

  // Transform API data to chart format
  const chartData = distribution
    ? Object.entries(distribution)
        .filter(([, value]) => value > 0)
        .map(([key, value]) => ({
          name: DISASTER_TYPE_CONFIG[key]?.name || key,
          value: value,
          color: DISASTER_TYPE_CONFIG[key]?.color || "hsl(var(--chart-5))",
        }))
    : [];

  if (isLoading) {
    return (
      <div className="glass rounded-xl p-5 animate-fade-in" style={{ animationDelay: "250ms" }}>
        <h3 className="text-lg font-semibold mb-4">Phân bố theo loại thiên tai</h3>
        <div className="h-48 flex items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error || chartData.length === 0) {
    return (
      <div className="glass rounded-xl p-5 animate-fade-in" style={{ animationDelay: "250ms" }}>
        <h3 className="text-lg font-semibold mb-4">Phân bố theo loại thiên tai</h3>
        <div className="h-48 flex items-center justify-center text-muted-foreground">
          {error ? "Không thể tải dữ liệu" : "Chưa có dữ liệu"}
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl p-5 animate-fade-in" style={{ animationDelay: "250ms" }}>
      <h3 className="text-lg font-semibold mb-4">Phân bố theo loại thiên tai</h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
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
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-2 gap-2 mt-4">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center gap-2">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-xs text-muted-foreground">{item.name}</span>
            <span className="text-xs font-semibold ml-auto">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
