import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { SectionCard } from "./section-card";
import type { FocusItem, FocusPriority } from "./types";

const PRIORITY_RANK: Record<FocusPriority, number> = {
  low: 0,
  medium: 1,
  high: 2,
};

const PRIORITY_META: Record<
  FocusPriority,
  { label: string; dotClass: string }
> = {
  low: { label: "Ready", dotClass: "bg-emerald-500" },
  medium: { label: "Needs attention", dotClass: "bg-amber-500" },
  high: { label: "Blocked", dotClass: "bg-red-500" },
};

type TodayFocusProps = {
  items: FocusItem[];
};

export function TodayFocus({ items }: TodayFocusProps) {
  const ordered = [...items].sort(
    (a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority],
  );

  return (
    <SectionCard
      title="Today's Focus"
      description="Prioritized by what's ready, blocked, or needs work."
    >
      <ul className="divide-y divide-border/60">
        {ordered.map((item) => {
          const meta = PRIORITY_META[item.priority];
          const primary = item.priority === "low";

          return (
            <li key={item.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
              <span
                aria-hidden="true"
                className={cn("size-2 shrink-0 rounded-full", meta.dotClass)}
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{item.label}</p>
                <p className="text-xs text-muted-foreground">{meta.label}</p>
              </div>
              <Button asChild size="sm" variant={primary ? "default" : "outline"}>
                <Link href={item.href}>
                  {item.actionLabel}
                  <ArrowRight data-icon="inline-end" className="size-3.5" />
                </Link>
              </Button>
            </li>
          );
        })}
      </ul>
    </SectionCard>
  );
}
