export function ContentSkeleton() {
  return (
    <div aria-hidden="true" className="flex flex-col gap-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <div className="h-7 w-40 animate-pulse rounded-full bg-muted" />
          <div className="h-4 w-80 max-w-full animate-pulse rounded-full bg-muted" />
        </div>
        <div className="flex gap-2">
          <div className="h-8 w-40 animate-pulse rounded-lg bg-muted" />
          <div className="h-8 w-32 animate-pulse rounded-lg bg-muted" />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="rounded-xl border border-border bg-card p-4">
            <div className="h-3 w-24 animate-pulse rounded-full bg-muted" />
            <div className="mt-3 h-7 w-16 animate-pulse rounded-full bg-muted" />
            <div className="mt-3 h-3 w-28 animate-pulse rounded-full bg-muted" />
          </div>
        ))}
      </div>

      <div className="h-8 animate-pulse rounded-lg bg-muted" />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="h-4 w-20 animate-pulse rounded-full bg-muted" />
          <div className="mt-4 flex flex-col gap-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-14 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="h-12 animate-pulse rounded-lg bg-muted" />
          <div className="mt-4 flex flex-col gap-3">
            <div className="h-4 w-32 animate-pulse rounded-full bg-muted" />
            <div className="h-8 animate-pulse rounded-lg bg-muted" />
            <div className="h-24 animate-pulse rounded-lg bg-muted" />
            <div className="h-8 animate-pulse rounded-lg bg-muted" />
          </div>
        </div>
      </div>
    </div>
  );
}
