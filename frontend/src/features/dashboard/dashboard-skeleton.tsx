export function DashboardSkeleton() {
  return (
    <div aria-hidden="true" className="flex flex-col gap-8">
      <div className="space-y-2">
        <div className="h-3 w-44 animate-pulse rounded-full bg-muted" />
        <div className="h-7 w-64 animate-pulse rounded-full bg-muted" />
        <div className="h-4 w-96 max-w-full animate-pulse rounded-full bg-muted" />
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="rounded-xl border border-border bg-card p-4">
            <div className="h-3 w-24 animate-pulse rounded-full bg-muted" />
            <div className="mt-3 h-7 w-16 animate-pulse rounded-full bg-muted" />
            <div className="mt-3 h-3 w-28 animate-pulse rounded-full bg-muted" />
          </div>
        ))}
      </div>

      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="rounded-xl border border-border bg-card p-5">
          <div className="h-4 w-40 animate-pulse rounded-full bg-muted" />
          <div className="mt-5 flex flex-col gap-3">
            <div className="h-9 animate-pulse rounded-lg bg-muted" />
            <div className="h-9 animate-pulse rounded-lg bg-muted" />
            <div className="h-9 animate-pulse rounded-lg bg-muted" />
          </div>
        </div>
      ))}
    </div>
  );
}
