import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Metric, MetricTone } from "./types";

const DELTA_TONES: Record<MetricTone, string> = {
  positive: "text-emerald-600 dark:text-emerald-400",
  attention: "text-amber-600 dark:text-amber-400",
  neutral: "text-muted-foreground",
};

type MetricCardProps = {
  metric: Metric;
  icon: LucideIcon;
};

export function MetricCard({ metric, icon: Icon }: MetricCardProps) {
  const tone = metric.deltaTone ?? "neutral";

  return (
    <div className="flex h-full flex-col rounded-xl border border-border bg-card p-4">
      <div className="flex items-start justify-between gap-2">
        <dl className="min-w-0">
          <dt className="truncate text-xs font-medium text-muted-foreground">
            {metric.label}
          </dt>
          <dd className="mt-2 text-3xl font-semibold tracking-tight tabular-nums">
            {metric.value}
          </dd>
        </dl>
        <span className="flex size-8 shrink-0 items-center justify-center rounded-lg border bg-muted/50 text-muted-foreground">
          <Icon className="size-4" aria-hidden="true" />
        </span>
      </div>
      {metric.delta && (
        <p className={cn("mt-3 text-xs tabular-nums", DELTA_TONES[tone])}>
          {metric.delta}
        </p>
      )}
    </div>
  );
}
