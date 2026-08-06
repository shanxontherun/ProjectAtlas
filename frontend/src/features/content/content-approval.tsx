"use client";

import { CheckCircle2, PenLine, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ContentStatusBadge } from "./content-status-badge";
import type { ContentItem } from "./types";

type ContentApprovalProps = {
  item: ContentItem | null;
  onApprove: () => void;
  onNeedsChanges: () => void;
  onQueue: () => void;
};

function getHint(item: ContentItem | null) {
  if (!item) return "Select a product from the queue to make a review decision.";
  switch (item.status) {
    case "waiting":
      return "This product hasn't been generated yet — generate it before reviewing.";
    case "generating":
      return "Content is still being generated. It will be ready to review shortly.";
    case "needs-review":
      return "Approve this content, request changes, or send it to the Creative Studio.";
    case "approved":
      return "This content is approved. Queue it for the Creative Studio or request more changes.";
    case "queued":
      return "This content has already been queued for the Creative Studio.";
  }
}

export function ContentApproval({
  item,
  onApprove,
  onNeedsChanges,
  onQueue,
}: ContentApprovalProps) {
  const reviewable = item?.status === "needs-review";
  const changesEnabled = item?.status === "needs-review" || item?.status === "approved";

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="flex flex-col gap-1">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold tracking-tight">
            Review Decision
          </h2>
          {item && <ContentStatusBadge status={item.status} />}
        </div>
        <p className="text-xs text-muted-foreground">
          {item ? `${item.productName} — ${getHint(item)}` : getHint(item)}
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          onClick={onApprove}
          disabled={!reviewable}
          className="flex-1 sm:flex-none"
        >
          <CheckCircle2 data-icon="inline-start" className="size-4" />
          Approve
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onNeedsChanges}
          disabled={!changesEnabled}
          className="flex-1 sm:flex-none"
        >
          <PenLine data-icon="inline-start" className="size-4" />
          Needs Changes
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onQueue}
          disabled={!changesEnabled}
          className="flex-1 sm:flex-none"
        >
          <Send data-icon="inline-start" className="size-4" />
          Queue for Creative Studio
        </Button>
      </div>
    </section>
  );
}
