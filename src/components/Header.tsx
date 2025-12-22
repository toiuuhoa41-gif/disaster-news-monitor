import { Activity, Bell, RefreshCw, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useState } from "react";

export function Header() {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 2000);
  };

  return (
    <header className="glass border-b border-border/50 sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center glow-danger">
                <Activity className="h-5 w-5 text-primary" />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-success rounded-full border-2 border-card animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                <span className="text-gradient-danger">Disaster</span>
                <span className="text-foreground"> Monitor</span>
              </h1>
              <p className="text-xs text-muted-foreground">
                Hệ thống giám sát tin thiên tai thời gian thực
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-success/10 border border-success/20">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
              <span className="text-xs font-medium text-success">Đang hoạt động</span>
            </div>
            
            <Button
              variant="ghost"
              size="icon"
              className="relative"
              onClick={handleRefresh}
            >
              <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            </Button>

            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-4 w-4" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-primary rounded-full" />
            </Button>

            <Button variant="ghost" size="icon">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
