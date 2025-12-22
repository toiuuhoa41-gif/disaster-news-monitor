import { cn } from "@/lib/utils";
import { DISASTER_KEYWORDS } from "@/data/mockData";

const categoryConfig: Record<string, { label: string; color: string }> = {
  weather: { label: "Thời tiết", color: "bg-chart-1/20 text-chart-1 border-chart-1/30" },
  flood: { label: "Lũ lụt", color: "bg-chart-2/20 text-chart-2 border-chart-2/30" },
  drought: { label: "Hạn hán", color: "bg-chart-3/20 text-chart-3 border-chart-3/30" },
  earthquake: { label: "Động đất", color: "bg-chart-4/20 text-chart-4 border-chart-4/30" },
  general: { label: "Chung", color: "bg-chart-5/20 text-chart-5 border-chart-5/30" },
};

export function KeywordCloud() {
  return (
    <div className="glass rounded-xl p-5 animate-fade-in" style={{ animationDelay: "200ms" }}>
      <h3 className="text-lg font-semibold mb-4">Từ khóa thiên tai</h3>
      <div className="space-y-4">
        {Object.entries(DISASTER_KEYWORDS).map(([category, keywords]) => {
          const config = categoryConfig[category];
          return (
            <div key={category}>
              <div className="flex items-center gap-2 mb-2">
                <div className={cn("w-2 h-2 rounded-full", config.color.split(" ")[0].replace("/20", ""))} />
                <span className="text-sm font-medium text-muted-foreground">{config.label}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className={cn(
                      "px-2.5 py-1 text-xs rounded-lg border transition-all hover:scale-105 cursor-default",
                      config.color
                    )}
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
