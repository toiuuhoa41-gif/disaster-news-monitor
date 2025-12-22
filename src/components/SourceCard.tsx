import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Globe, Clock, FileText } from "lucide-react";

interface SourceCardProps {
  name: string;
  domain: string;
  status: "active" | "warning" | "error";
  articlesCount: number;
  lastCrawl: string;
  categories: string[];
  index: number;
}

export function SourceCard({
  name,
  domain,
  status,
  articlesCount,
  lastCrawl,
  categories,
  index,
}: SourceCardProps) {
  const statusConfig = {
    active: {
      label: "Hoạt động",
      className: "bg-success/20 text-success border-success/30",
      dotClass: "bg-success",
    },
    warning: {
      label: "Chậm",
      className: "bg-warning/20 text-warning border-warning/30",
      dotClass: "bg-warning",
    },
    error: {
      label: "Lỗi",
      className: "bg-primary/20 text-primary border-primary/30",
      dotClass: "bg-primary",
    },
  };

  const config = statusConfig[status];

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      className="glass rounded-xl p-4 transition-all duration-300 hover:border-accent/30 animate-fade-in group"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
              <Globe className="h-5 w-5 text-accent" />
            </div>
            <div
              className={cn(
                "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-card",
                config.dotClass
              )}
            />
          </div>
          <div>
            <h3 className="font-semibold group-hover:text-accent transition-colors">
              {name}
            </h3>
            <p className="text-xs text-muted-foreground font-mono">{domain}</p>
          </div>
        </div>
        <Badge className={config.className}>{config.label}</Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="flex items-center gap-2 text-sm">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="text-muted-foreground">Bài viết:</span>
          <span className="font-semibold">{articlesCount}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-muted-foreground">Cập nhật:</span>
          <span className="font-mono text-xs">{formatTime(lastCrawl)}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {categories.map((cat) => (
          <span
            key={cat}
            className="px-2 py-0.5 text-xs rounded-md bg-secondary text-muted-foreground"
          >
            {cat}
          </span>
        ))}
      </div>
    </div>
  );
}
