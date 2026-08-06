"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { STATUS_META } from "./content-status-badge";
import type { ContentStatusFilter } from "./types";

const STATUS_FILTERS: { value: ContentStatusFilter; label: string }[] = [
  { value: "all", label: "All statuses" },
  { value: "waiting", label: STATUS_META.waiting.label },
  { value: "generating", label: STATUS_META.generating.label },
  { value: "needs-review", label: STATUS_META["needs-review"].label },
  { value: "approved", label: STATUS_META.approved.label },
  { value: "queued", label: STATUS_META.queued.label },
];

type ContentToolbarProps = {
  query: string;
  onQueryChange: (value: string) => void;
  status: ContentStatusFilter;
  onStatusChange: (value: ContentStatusFilter) => void;
  total: number;
  shown: number;
};

export function ContentToolbar({
  query,
  onQueryChange,
  status,
  onStatusChange,
  total,
  shown,
}: ContentToolbarProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="relative min-w-0 flex-1 sm:max-w-xs">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search products..."
          aria-label="Search products"
          className="pl-8"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Select
          value={status}
          onValueChange={(value) => onStatusChange(value as ContentStatusFilter)}
        >
          <SelectTrigger
            size="sm"
            aria-label="Filter by status"
            className="w-full sm:w-auto"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent align="start">
            {STATUS_FILTERS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs tabular-nums text-muted-foreground">
          Showing {shown} of {total}
        </p>
      </div>
    </div>
  );
}
