"use client";

import { Eye } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ProductImage } from "@/features/products/product-image";
import { ContentStatusBadge } from "./content-status-badge";
import type { ContentItem, ContentPriority } from "./types";

const PRIORITY_DOT: Record<ContentPriority, string> = {
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-emerald-500",
};

const PRIORITY_LABEL: Record<ContentPriority, string> = {
  high: "High priority",
  medium: "Medium priority",
  low: "Low priority",
};

type ContentQueueProps = {
  items: ContentItem[];
  selectedId: string | null;
  onSelect: (item: ContentItem) => void;
  onPreview: (item: ContentItem) => void;
  hasActiveFilters: boolean;
  onClearFilters: () => void;
};

export function ContentQueue({
  items,
  selectedId,
  onSelect,
  onPreview,
  hasActiveFilters,
  onClearFilters,
}: ContentQueueProps) {
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold tracking-tight">Queue</h2>
        <span className="text-xs tabular-nums text-muted-foreground">
          {items.length} {items.length === 1 ? "item" : "items"}
        </span>
      </header>

      {items.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed bg-muted/30 px-4 py-10 text-center">
          <p className="text-sm font-medium">No products in the queue</p>
          <p className="max-w-[20rem] text-xs text-muted-foreground">
            {hasActiveFilters
              ? "No products match your current search or status filter."
              : "Products waiting for AI content will appear here."}
          </p>
          {hasActiveFilters && (
            <Button size="sm" variant="outline" onClick={onClearFilters}>
              Clear filters
            </Button>
          )}
        </div>
      ) : (
        <ol className="flex flex-col gap-1.5">
          {items.map((item) => {
            const selected = item.id === selectedId;

            return (
              <li key={item.id} className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onSelect(item)}
                  aria-pressed={selected}
                  aria-label={`Open ${item.productName} in the editor`}
                  className={cn(
                    "relative flex min-w-0 flex-1 items-center gap-3 rounded-lg p-2.5 text-left outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50",
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
                      <span
                        className={cn(
                          "size-1.5 shrink-0 rounded-full",
                          PRIORITY_DOT[item.priority],
                        )}
                        aria-hidden="true"
                      />
                      <span className="sr-only">
                        {PRIORITY_LABEL[item.priority]}
                      </span>
                    </span>
                  </span>
                  <ContentStatusBadge status={item.status} />
                </button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Preview ${item.productName}`}
                  title="Preview"
                  onClick={() => onPreview(item)}
                  className="shrink-0"
                >
                  <Eye />
                </Button>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
