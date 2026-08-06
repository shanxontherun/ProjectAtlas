import { CheckCircle2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import { getReadiness } from "./creative-utils";
import type { CreativeItem } from "./types";

type ReadinessChecklistProps = {
  item: CreativeItem | null;
};

export function ReadinessChecklist({ item }: ReadinessChecklistProps) {
  const checklist = getReadiness(item);
  const total = checklist.length;
  const done = checklist.filter((entry) => entry.done).length;
  const ready = done === total;

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="space-y-0.5">
        <h2 className="text-sm font-semibold tracking-tight">
          Publishing Readiness
        </h2>
        <p className="text-xs text-muted-foreground">
          What is needed before this pin goes live.
        </p>
      </header>

      <ul className="flex flex-col gap-2">
        {checklist.map((entry) => (
          <li key={entry.id} className="flex items-center gap-2 text-xs">
            {entry.done ? (
              <CheckCircle2
                className="size-4 shrink-0 text-emerald-600 dark:text-emerald-400"
                aria-hidden="true"
              />
            ) : (
              <Circle
                className="size-4 shrink-0 text-muted-foreground/40"
                aria-hidden="true"
              />
            )}
            <span
              className={cn(
                "font-medium",
                entry.done ? "text-foreground" : "text-muted-foreground",
              )}
            >
              {entry.label}
            </span>
          </li>
        ))}
      </ul>

      <div
        className={cn(
          "rounded-lg border px-3 py-2 text-xs font-medium",
          ready
            ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
            : "border-border bg-muted/40 text-muted-foreground",
        )}
      >
        {ready ? "Ready for Publishing" : `${done} of ${total} complete`}
      </div>
    </section>
  );
}
