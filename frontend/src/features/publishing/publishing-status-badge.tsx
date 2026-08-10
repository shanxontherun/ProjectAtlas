import { cn } from "@/lib/utils";
import type { PublishQueueStatus, PublicationStatus } from "./types";

export type PublishStatus = PublishQueueStatus | PublicationStatus;

export const PUBLISH_STATUS_META: Record<
  PublishStatus,
  { label: string; badgeClass: string; dotClass: string }
> = {
  queued: {
    label: "Queued",
    badgeClass: "border-border bg-muted/60 text-muted-foreground",
    dotClass: "bg-muted-foreground",
  },
  scheduled: {
    label: "Scheduled",
    badgeClass: "border-chart-4/25 bg-chart-4/10 text-chart-4",
    dotClass: "bg-chart-4",
  },
  published: {
    label: "Published",
    badgeClass:
      "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    dotClass: "bg-emerald-500",
  },
  failed: {
    label: "Failed",
    badgeClass:
      "border-red-500/25 bg-red-500/10 text-red-600 dark:text-red-400",
    dotClass: "bg-red-500",
  },
  cancelled: {
    label: "Cancelled",
    badgeClass: "border-border bg-muted/60 text-muted-foreground",
    dotClass: "bg-muted-foreground",
  },
};

type PublishingStatusBadgeProps = {
  status: PublishStatus;
  className?: string;
};

export function PublishingStatusBadge({
  status,
  className,
}: PublishingStatusBadgeProps) {
  const meta = PUBLISH_STATUS_META[status];

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
