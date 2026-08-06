import { cn } from "@/lib/utils";

type ProgressBarProps = {
  value: number;
  showValue?: boolean;
  label?: string;
  thick?: boolean;
  className?: string;
};

export function ProgressBar({
  value,
  showValue = true,
  label,
  thick = false,
  className,
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      {label && (
        <span className="w-28 shrink-0 truncate text-xs text-muted-foreground">
          {label}
        </span>
      )}
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clamped}
        aria-label={label ?? "Workflow progress"}
        className={cn(
          "min-w-0 flex-1 overflow-hidden rounded-full bg-muted",
          thick ? "h-2.5" : "h-2",
        )}
      >
        <div
          className="h-full rounded-full bg-foreground transition-[width] duration-500 ease-out"
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showValue && (
        <span className="w-8 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
          {clamped}%
        </span>
      )}
    </div>
  );
}
