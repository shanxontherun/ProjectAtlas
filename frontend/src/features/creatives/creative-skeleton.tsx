export function CreativeSkeleton() {
  return (
    <div aria-hidden="true" className="flex flex-col gap-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <div className="h-7 w-44 animate-pulse rounded-full bg-muted" />
          <div className="h-4 w-80 max-w-full animate-pulse rounded-full bg-muted" />
        </div>
        <div className="flex gap-2">
          <div className="h-8 w-40 animate-pulse rounded-lg bg-muted" />
          <div className="h-8 w-32 animate-pulse rounded-lg bg-muted" />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="rounded-xl border border-border bg-card p-4">
            <div className="h-3 w-24 animate-pulse rounded-full bg-muted" />
            <div className="mt-3 h-7 w-14 animate-pulse rounded-full bg-muted" />
            <div className="mt-3 h-3 w-28 animate-pulse rounded-full bg-muted" />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_3fr]">
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
          <div className="h-4 w-28 animate-pulse rounded-full bg-muted" />
          <div className="flex flex-col gap-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-14 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-3">
            <div className="size-11 animate-pulse rounded-lg bg-muted" />
            <div className="space-y-2">
              <div className="h-4 w-48 animate-pulse rounded-full bg-muted" />
              <div className="h-3 w-32 animate-pulse rounded-full bg-muted" />
            </div>
          </div>
          <div className="flex h-[24rem] animate-pulse items-center justify-center rounded-xl bg-muted/40">
            <div className="h-3/4 w-2/3 animate-pulse rounded-xl bg-muted" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5">
            <div className="h-4 w-28 animate-pulse rounded-full bg-muted" />
            <div className="h-10 w-16 animate-pulse rounded-full bg-muted" />
            <div className="h-3 w-full animate-pulse rounded-full bg-muted" />
            <div className="h-3 w-3/4 animate-pulse rounded-full bg-muted" />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5">
          <div className="h-4 w-24 animate-pulse rounded-full bg-muted" />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-32 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5">
          <div className="h-4 w-24 animate-pulse rounded-full bg-muted" />
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-8 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </div>

      <div className="h-16 animate-pulse rounded-xl bg-muted" />
    </div>
  );
}
