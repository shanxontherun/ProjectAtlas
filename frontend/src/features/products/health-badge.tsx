import { cn } from "@/lib/utils";
import { HEALTH_META, type ProductHealth } from "./types";

type HealthBadgeProps = {
  health: ProductHealth;
  className?: string;
};

export function HealthBadge({ health, className }: HealthBadgeProps) {
  const meta = HEALTH_META[health];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
        meta.badgeClass,
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", meta.dotClass)} aria-hidden="true" />
      {meta.label}
    </span>
  );
}
