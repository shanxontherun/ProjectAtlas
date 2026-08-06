import { cn } from "@/lib/utils";

export function ProductSkeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "flex flex-col overflow-hidden rounded-xl border border-border bg-card",
        className,
      )}
    >
      <div className="aspect-[4/3] animate-pulse bg-muted" />
      <div className="flex flex-col gap-3 p-4">
        <div className="flex flex-col gap-1.5">
          <div className="h-2.5 w-1/3 animate-pulse rounded-full bg-muted" />
          <div className="h-4 w-3/4 animate-pulse rounded-full bg-muted" />
        </div>
        <div className="h-3 w-1/2 animate-pulse rounded-full bg-muted" />
        <div className="h-2 w-full animate-pulse rounded-full bg-muted" />
        <div className="h-3.5 w-24 animate-pulse rounded-full bg-muted" />
      </div>
    </div>
  );
}
