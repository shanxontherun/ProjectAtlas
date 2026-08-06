import { Fragment } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { SectionCard } from "./section-card";
import type { PipelineStage } from "./types";

type PipelineOverviewProps = {
  stages: PipelineStage[];
};

export function PipelineOverview({ stages }: PipelineOverviewProps) {
  const lastKey = stages[stages.length - 1]?.key;

  return (
    <SectionCard
      title="Pipeline Overview"
      description="Products currently in each stage of the workflow."
    >
      <ol className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-0">
        {stages.map((stage, index) => {
          const isLast = stage.key === lastKey;

          return (
            <Fragment key={stage.key}>
              {index > 0 && (
                <li
                  aria-hidden="true"
                  className="flex items-center justify-center lg:shrink-0"
                >
                  <ChevronRight className="size-4 rotate-90 text-muted-foreground/50 lg:rotate-0" />
                </li>
              )}
              <li className="flex items-center gap-3 lg:flex-1 lg:flex-col lg:gap-2">
                <span
                  className={cn(
                    "flex size-10 shrink-0 items-center justify-center rounded-full border text-base font-semibold tabular-nums",
                    isLast
                      ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                      : "border-border bg-muted/50 text-foreground",
                  )}
                >
                  {stage.count}
                </span>
                <span className="text-xs font-medium text-muted-foreground lg:text-center">
                  {stage.label}
                </span>
              </li>
            </Fragment>
          );
        })}
      </ol>
    </SectionCard>
  );
}
