export function AccountsSkeleton() {
  return (
    <div aria-hidden="true" className="flex flex-col gap-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <div className="h-7 w-40 animate-pulse rounded-full bg-muted" />
          <div className="h-4 w-96 max-w-full animate-pulse rounded-full bg-muted" />
        </div>
        <div className="h-8 w-24 animate-pulse rounded-lg bg-muted" />
      </div>

      <div className="flex flex-col gap-6">
        {Array.from({ length: 3 }).map((_, sectionIndex) => (
          <div
            key={sectionIndex}
            className="rounded-xl border border-border bg-card p-5"
          >
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="h-4 w-36 animate-pulse rounded-full bg-muted" />
                <div className="h-3 w-72 max-w-full animate-pulse rounded-full bg-muted" />
              </div>
              <div className="h-6 w-24 animate-pulse rounded-full bg-muted" />
            </div>
            <div className="mt-4 flex flex-col gap-3">
              {Array.from({ length: sectionIndex === 0 ? 2 : 1 }).map(
                (_, index) => (
                  <div
                    key={index}
                    className="h-16 animate-pulse rounded-xl bg-muted/50"
                  />
                ),
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
