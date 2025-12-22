import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Clock, ExternalLink } from "lucide-react";

interface ArticleCardProps {
  title: string;
  source: string;
  category: string;
  publishedAt: string;
  keywords: string[];
  severity: "high" | "medium" | "low";
  index: number;
}

export function ArticleCard({
  title,
  source,
  category,
  publishedAt,
  keywords,
  severity,
  index,
}: ArticleCardProps) {
  const severityConfig = {
    high: {
      label: "Nghiêm trọng",
      className: "bg-primary/20 text-primary border-primary/30",
      iconClass: "text-primary",
      borderClass: "border-l-primary",
    },
    medium: {
      label: "Trung bình",
      className: "bg-warning/20 text-warning border-warning/30",
      iconClass: "text-warning",
      borderClass: "border-l-warning",
    },
    low: {
      label: "Thấp",
      className: "bg-muted text-muted-foreground border-border",
      iconClass: "text-muted-foreground",
      borderClass: "border-l-muted-foreground",
    },
  };

  const config = severityConfig[severity];

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) {
      return `${diffMins} phút trước`;
    }
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) {
      return `${diffHours} giờ trước`;
    }
    return date.toLocaleDateString("vi-VN");
  };

  return (
    <div
      className={cn(
        "glass rounded-xl p-4 transition-all duration-300 hover:border-accent/30 animate-slide-in-right border-l-4 group cursor-pointer",
        config.borderClass
      )}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <div className="flex items-start gap-3">
        {severity === "high" && (
          <div className="relative flex-shrink-0 mt-1">
            <AlertTriangle className={cn("h-5 w-5", config.iconClass)} />
            <div className="absolute inset-0 animate-pulse-ring">
              <AlertTriangle className={cn("h-5 w-5", config.iconClass, "opacity-50")} />
            </div>
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-medium text-sm leading-snug group-hover:text-accent transition-colors line-clamp-2">
              {title}
            </h3>
            <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
          </div>

          <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
            <span className="font-medium text-foreground/80">{source}</span>
            <span>•</span>
            <span>{category}</span>
            <span>•</span>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatTime(publishedAt)}
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={config.className}>{config.label}</Badge>
            {keywords.slice(0, 2).map((keyword) => (
              <span
                key={keyword}
                className="px-2 py-0.5 text-xs rounded-md bg-accent/10 text-accent border border-accent/20"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
