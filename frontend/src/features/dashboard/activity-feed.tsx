import {
  CheckCircle2,
  ImageIcon,
  Package,
  Send,
  Sparkles,
  Tag,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { SectionCard } from "./section-card";
import type { ActivityIcon, ActivityItem } from "./types";

const ACTIVITY_ICONS: Record<ActivityIcon, LucideIcon> = {
  image: ImageIcon,
  ai: Sparkles,
  publish: Send,
  import: Package,
  category: Tag,
  check: CheckCircle2,
};

const ACTIVITY_TONES: Record<ActivityIcon, string> = {
  image: "border-chart-3/25 bg-chart-3/10 text-chart-3",
  ai: "border-chart-1/25 bg-chart-1/10 text-chart-1",
  publish: "border-chart-2/25 bg-chart-2/10 text-chart-2",
  import: "border-border bg-muted/50 text-muted-foreground",
  category: "border-amber-500/25 bg-amber-500/10 text-amber-600 dark:text-amber-400",
  check: "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
};

type ActivityFeedProps = {
  items: ActivityItem[];
};

export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <SectionCard title="Recent Activity" description="The latest pipeline events across your workspace.">
      <ol className="divide-y divide-border/60">
        {items.map((item) => {
          const Icon = ACTIVITY_ICONS[item.icon];
          const tone = ACTIVITY_TONES[item.icon];

          return (
            <li
              key={item.id}
              className="flex items-start gap-3 py-2.5 first:pt-0 last:pb-0"
            >
              <span
                className={cn(
                  "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border",
                  tone,
                )}
              >
                <Icon className="size-4" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1 space-y-0.5">
                <p className="text-sm leading-tight font-medium">{item.title}</p>
                <p className="text-xs leading-snug text-muted-foreground">
                  {item.description}
                </p>
              </div>
              <span className="shrink-0 text-[11px] tabular-nums text-muted-foreground">
                {item.time}
              </span>
            </li>
          );
        })}
      </ol>
    </SectionCard>
  );
}
