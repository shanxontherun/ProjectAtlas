import { cn } from "@/lib/utils";
import type { ContentStatus } from "./types";

export const STATUS_META: Record<
  ContentStatus,
  { label: string; badgeClass: string; dotClass: string }
> = {
  waiting: {
    label: "Waiting",
    badgeClass: "border-border bg-muted/60 text-muted-foreground",
    dotClass: "bg-muted-foreground",
  },
  generating: {
    label: "Generating",
    badgeClass: "border-chart-1/25 bg-chart-1/10 text-chart-1",
    dotClass: "bg-chart-1",
  },
  "needs-review": {
    label: "Needs Review",
    badgeClass:
      "border-amber-500/25 bg-amber-500/10 text-amber-600 dark:text-amber-400",
    dotClass: "bg-amber-500",
  },
  approved: {
    label: "Approved",
    badgeClass:
      "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    dotClass: "bg-emerald-500",
  },
  queued: {
    label: "Queued",
    badgeClass: "border-chart-2/25 bg-chart-2/10 text-chart-2",
    dotClass: "bg-chart-2",
  },
};

type ContentStatusBadgeProps = {
  status: ContentStatus;
  className?: string;
};

export function ContentStatusBadge({
  status,
  className,
}: ContentStatusBadgeProps) {
  const meta = STATUS_META[status];

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
        meta.badgeClass,
        className,
      )}
    >
      <span
        className={cn("size-1.5 rounded-full", meta.dotClass)}
        aria-hidden="true"
      />
      {meta.label}
    </span>
  );
}
