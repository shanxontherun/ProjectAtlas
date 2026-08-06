"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ContentStatusBadge } from "@/features/content/content-status-badge";
import { ProductImage } from "@/features/products/product-image";
import { TEMPLATE_BY_ID } from "./mock-data";
import type { CreativeItem, CreativePriority } from "./types";

const PRIORITY_META: Record<CreativePriority, { label: string; dotClass: string }> = {
  high: { label: "High priority", dotClass: "bg-red-500" },
  medium: { label: "Medium priority", dotClass: "bg-amber-500" },
  low: { label: "Low priority", dotClass: "bg-emerald-500" },
};

type CreativeQueueProps = {
  items: CreativeItem[];
  selectedId: string | null;
  onSelect: (item: CreativeItem) => void;
};

export function CreativeQueue({ items, selectedId, onSelect }: CreativeQueueProps) {
  const [collapsed, setCollapsed] = useState(false);
  const reviewCount = items.filter((item) => item.status === "needs-review").length;

  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <h2 className="text-sm font-semibold tracking-tight">Creative Queue</h2>
          {reviewCount > 0 && (
            <span className="rounded-full border border-amber-500/25 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
              {reviewCount} to review
            </span>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <span className="text-xs tabular-nums text-muted-foreground">
            {items.length} {items.length === 1 ? "item" : "items"}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label={collapsed ? "Expand queue" : "Collapse queue"}
            aria-expanded={!collapsed}
            onClick={() => setCollapsed((current) => !current)}
            className="lg:hidden"
          >
            <ChevronDown
              className={cn("transition-transform", collapsed ? "" : "rotate-180")}
            />
          </Button>
        </div>
      </header>

      {items.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed bg-muted/30 px-4 py-10 text-center">
          <p className="text-sm font-medium">No creatives in the queue</p>
          <p className="max-w-[20rem] text-xs text-muted-foreground">
            Products waiting for review will appear here.
          </p>
        </div>
      ) : (
        <ol className={cn("flex flex-col gap-1.5", collapsed && "hidden lg:flex")}>
          {items.map((item) => {
            const selected = item.id === selectedId;
            const priority = PRIORITY_META[item.priority];

            return (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => onSelect(item)}
                  aria-pressed={selected}
                  aria-label={`Open ${item.productName} in Creative Studio`}
                  className={cn(
                    "relative flex min-w-0 w-full items-center gap-3 rounded-lg p-2.5 text-left outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50",
                    selected
                      ? "bg-muted ring-1 ring-ring/40"
                      : "hover:bg-muted/50",
                  )}
                >
                  {selected && (
                    <span
                      aria-hidden="true"
                      className="absolute top-1/2 left-0 h-6 w-[3px] -translate-y-1/2 rounded-r-full bg-primary"
                    />
                  )}
                  <span className="relative size-10 shrink-0 overflow-hidden rounded-md border bg-muted">
                    <ProductImage src={item.imageUrl} alt={item.productName} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span
                      className={cn(
                        "block truncate text-sm",
                        selected ? "font-semibold" : "font-medium",
                      )}
                    >
                      {item.productName}
                    </span>
                    <span className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                      <span className="truncate">{item.category}</span>
                      <span aria-hidden="true">·</span>
                      <span className="truncate">
                        {TEMPLATE_BY_ID[item.templateId].name}
                      </span>
                      <span aria-hidden="true">·</span>
                      <span
                        className={cn("size-1.5 shrink-0 rounded-full", priority.dotClass)}
                        aria-hidden="true"
                      />
                      <span className="sr-only">{priority.label}</span>
                    </span>
                  </span>
                  <ContentStatusBadge status={item.status} />
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
