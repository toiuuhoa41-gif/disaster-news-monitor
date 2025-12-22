import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: "default" | "danger" | "accent" | "success";
  className?: string;
}

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = "default",
  className,
}: StatCardProps) {
  const variantStyles = {
    default: "border-border/50",
    danger: "border-primary/30 glow-danger",
    accent: "border-accent/30 glow-accent",
    success: "border-success/30 glow-success",
  };

  const iconStyles = {
    default: "text-muted-foreground bg-muted",
    danger: "text-primary bg-primary/20",
    accent: "text-accent bg-accent/20",
    success: "text-success bg-success/20",
  };

  return (
    <div
      className={cn(
        "glass rounded-xl p-5 transition-all duration-300 hover:scale-[1.02] animate-fade-in",
        variantStyles[variant],
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold tracking-tight">{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
          {trend && (
            <p
              className={cn(
                "text-xs font-medium",
                trend.isPositive ? "text-success" : "text-primary"
              )}
            >
              {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}% so với hôm qua
            </p>
          )}
        </div>
        <div className={cn("p-3 rounded-lg", iconStyles[variant])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}
