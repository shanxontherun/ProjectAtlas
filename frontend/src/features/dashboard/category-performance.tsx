import { ProgressBar } from "@/features/products/progress-bar";
import { SectionCard } from "./section-card";
import type { CategoryPerformance as CategoryPerformanceRow } from "./types";

type CategoryPerformanceProps = {
  categories: CategoryPerformanceRow[];
};

export function CategoryPerformance({ categories }: CategoryPerformanceProps) {
  return (
    <SectionCard
      title="Category Performance"
      description="Ready-to-publish progress by product category."
    >
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {categories.map((category) => {
          const percent =
            category.products > 0
              ? Math.round((category.ready / category.products) * 100)
              : 0;

          return (
            <li
              key={category.id}
              className="flex flex-col gap-3 rounded-lg border border-border bg-background p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-sm font-medium">{category.name}</p>
                <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                  {category.products} products
                </span>
              </div>
              <div className="flex items-end justify-between gap-2">
                <span className="text-xs text-muted-foreground">
                  Ready to publish
                </span>
                <span className="text-sm font-semibold tabular-nums text-foreground">
                  {percent}%
                  <span className="ml-1 text-xs font-normal text-muted-foreground">
                    ({category.ready}/{category.products})
                  </span>
                </span>
              </div>
              <ProgressBar value={percent} showValue={false} thick />
            </li>
          );
        })}
      </ul>
    </SectionCard>
  );
}
