import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Clock, ExternalLink, MapPin } from "lucide-react";

interface ArticleCardProps {
  url: string;
  title: string;
  source: string;
  category?: string;
  publish_date?: string;
  publishDate?: Date | string;
  keywords?: string[];
  tags?: string[];
  severity?: "high" | "medium" | "low";
  index: number;
  region?: string;
  disaster_type?: string;
  summary?: string;
}

export function ArticleCard({
  url,
  title,
  source,
  category,
  publish_date,
  publishDate,
  keywords = [],
  tags = [],
  severity = "medium",
  index,
  region,
  disaster_type,
  summary,
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

  // Fallback to 'low' if severity is invalid
  const validSeverity = severity && severityConfig[severity] ? severity : 'low';
  const config = severityConfig[validSeverity];

  const formatTime = (dateInput: string | Date | undefined) => {
    if (!dateInput) return "Không rõ";
    
    const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
    if (isNaN(date.getTime())) return "Không rõ";
    
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 0) return "Vừa xong";
    if (diffMins < 60) {
      return `${diffMins} phút trước`;
    }
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) {
      return `${diffHours} giờ trước`;
    }
    return date.toLocaleDateString("vi-VN");
  };

  // Use publish_date or publishDate (for backward compatibility)
  const displayDate = publish_date || publishDate;
  const displayCategory = disaster_type || category || "Thiên tai";

  const handleClick = () => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div
      className={cn(
        "glass rounded-xl p-4 transition-all duration-300 hover:border-accent/30 animate-slide-in-right border-l-4 group cursor-pointer",
        config.borderClass
      )}
      style={{ animationDelay: `${index * 80}ms` }}
      onClick={handleClick}
      title={summary || title}
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

          <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground flex-wrap">
            <span className="font-medium text-foreground/80">{source}</span>
            <span>•</span>
            <span>{displayCategory}</span>
            {region && (
              <>
                <span>•</span>
                <div className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {region}
                </div>
              </>
            )}
            <span>•</span>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatTime(displayDate)}
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
