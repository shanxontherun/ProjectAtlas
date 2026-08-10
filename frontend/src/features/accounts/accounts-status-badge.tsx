import { cn } from "@/lib/utils";
import type { ConnectionStatus } from "./accounts-api";

type StatusMeta = {
  label: string;
  badgeClass: string;
  dotClass: string;
};

export const ACCOUNT_STATUS_META: Record<ConnectionStatus, StatusMeta> = {
  CONNECTED: {
    label: "Connected",
    badgeClass:
      "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    dotClass: "bg-emerald-500",
  },
  CONNECTING: {
    label: "Connecting",
    badgeClass: "border-chart-4/25 bg-chart-4/10 text-chart-4",
    dotClass: "bg-chart-4",
  },
  CONFIGURED: {
    label: "Configured",
    badgeClass: "border-sky-500/25 bg-sky-500/10 text-sky-600 dark:text-sky-400",
    dotClass: "bg-sky-500",
  },
  NOT_CONNECTED: {
    label: "Not connected",
    badgeClass: "border-border bg-muted/60 text-muted-foreground",
    dotClass: "bg-muted-foreground",
  },
  NOT_CONFIGURED: {
    label: "Not configured",
    badgeClass: "border-border bg-muted/60 text-muted-foreground",
    dotClass: "bg-muted-foreground",
  },
  ERROR: {
    label: "Error",
    badgeClass:
      "border-red-500/25 bg-red-500/10 text-red-600 dark:text-red-400",
    dotClass: "bg-red-500",
  },
  DISCONNECTED: {
    label: "Disconnected",
    badgeClass: "border-border bg-muted/60 text-muted-foreground",
    dotClass: "bg-muted-foreground",
  },
};

type AccountStatusBadgeProps = {
  status: ConnectionStatus;
  className?: string;
};

export function AccountStatusBadge({
  status,
  className,
}: AccountStatusBadgeProps) {
  const meta = ACCOUNT_STATUS_META[status];

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
