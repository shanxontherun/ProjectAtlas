import { Sparkles } from "lucide-react";
import type { CreativeItem } from "./types";

const RECOMMENDED_TEMPLATE = "Minimal";
const EXPECTED_ENGAGEMENT = "+18%";

type AtlasRecommendationProps = {
  item: CreativeItem | null;
};

export function AtlasRecommendation({ item }: AtlasRecommendationProps) {
  const category = item?.category
    ? `Historically performs well for the ${item.category.toLowerCase()} category.`
    : "Historically performs well for this category.";

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="flex items-center gap-2">
        <span className="flex size-6 items-center justify-center rounded-md border bg-muted/50 text-muted-foreground">
          <Sparkles className="size-3.5" aria-hidden="true" />
        </span>
        <h2 className="text-sm font-semibold tracking-tight">
          Atlas Recommendation
        </h2>
      </header>

      <div className="flex flex-col gap-4">
        <div>
          <p className="text-xs text-muted-foreground">Recommended template</p>
          <p className="mt-1 text-sm font-semibold tracking-tight">
            {RECOMMENDED_TEMPLATE}
          </p>
        </div>

        <div>
          <p className="text-xs text-muted-foreground">Reason</p>
          <p className="mt-1 text-sm leading-relaxed">{category}</p>
        </div>

        <div>
          <p className="text-xs text-muted-foreground">Expected engagement</p>
          <p className="mt-1 text-xl leading-none font-semibold tracking-tight tabular-nums text-emerald-600 dark:text-emerald-400">
            {EXPECTED_ENGAGEMENT}
          </p>
        </div>
      </div>
    </section>
  );
}
