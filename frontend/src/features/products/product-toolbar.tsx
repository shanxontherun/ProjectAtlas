"use client";

import { LayoutGrid, List, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { WORKFLOW_STAGES } from "./types";
import type { SortKey } from "./product-utils";

export type ProductsViewMode = "grid" | "list";

type ToolbarSelectProps<T extends string> = {
  value: T;
  onValueChange: (value: T) => void;
  items: { value: T; label: string }[];
  ariaLabel: string;
  className?: string;
};

function ToolbarSelect<T extends string>({
  value,
  onValueChange,
  items,
  ariaLabel,
  className,
}: ToolbarSelectProps<T>) {
  return (
    <Select value={value} onValueChange={(next) => onValueChange(next as T)}>
      <SelectTrigger
        size="sm"
        aria-label={ariaLabel}
        className={cn("w-full sm:w-auto", className)}
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent align="start">
        {items.map((item) => (
          <SelectItem key={item.value} value={item.value}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

type ProductToolbarProps = {
  search: string;
  onSearchChange: (value: string) => void;
  categories: string[];
  category: string;
  onCategoryChange: (value: string) => void;
  stage: string;
  onStageChange: (value: string) => void;
  sort: SortKey;
  onSortChange: (value: SortKey) => void;
  view: ProductsViewMode;
  onViewChange: (view: ProductsViewMode) => void;
};

export function ProductToolbar({
  search,
  onSearchChange,
  categories,
  category,
  onCategoryChange,
  stage,
  onStageChange,
  sort,
  onSortChange,
  view,
  onViewChange,
}: ProductToolbarProps) {
  const sortItems: { value: SortKey; label: string }[] = [
    { value: "recommended", label: "Recommended" },
    { value: "name", label: "Name (A-Z)" },
    { value: "price-asc", label: "Price (low to high)" },
    { value: "price-desc", label: "Price (high to low)" },
    { value: "rating", label: "Top rated" },
    { value: "progress", label: "Most progress" },
  ];

  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="relative min-w-0 flex-1 lg:max-w-sm">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search products..."
          aria-label="Search products"
          className="pl-8"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <ToolbarSelect
          value={category}
          onValueChange={onCategoryChange}
          ariaLabel="Filter by category"
          items={[
            { value: "all", label: "All categories" },
            ...categories.map((categoryName) => ({
              value: categoryName,
              label: categoryName,
            })),
          ]}
        />
        <ToolbarSelect
          value={stage}
          onValueChange={onStageChange}
          ariaLabel="Filter by workflow stage"
          items={[
            { value: "all", label: "All stages" },
            ...WORKFLOW_STAGES.map((stageItem) => ({
              value: stageItem.key,
              label: stageItem.label,
            })),
          ]}
        />
        <ToolbarSelect
          value={sort}
          onValueChange={onSortChange}
          ariaLabel="Sort products"
          items={sortItems}
        />

        <div
          role="group"
          aria-label="View"
          className="flex items-center gap-0.5 rounded-lg border border-input bg-background p-0.5"
        >
          <button
            type="button"
            onClick={() => onViewChange("grid")}
            aria-pressed={view === "grid"}
            aria-label="Grid view"
            title="Grid view"
            className={cn(
              "flex size-7 items-center justify-center rounded-md transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
              view === "grid"
                ? "bg-muted text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <LayoutGrid className="size-4" />
          </button>
          <button
            type="button"
            onClick={() => onViewChange("list")}
            aria-pressed={view === "list"}
            aria-label="List view"
            title="List view"
            className={cn(
              "flex size-7 items-center justify-center rounded-md transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
              view === "list"
                ? "bg-muted text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <List className="size-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
