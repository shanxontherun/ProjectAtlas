"use client";

import { CheckCircle2, CopyPlus, RefreshCw, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ContentStatusBadge } from "@/features/content/content-status-badge";
import { ProductImage } from "@/features/products/product-image";
import type { CreativeItem } from "./types";

function getHint(item: CreativeItem | null) {
  if (!item) return "Select a creative from the queue to start reviewing.";
  switch (item.status) {
    case "waiting":
      return "This creative hasn't been generated yet — generate it before reviewing.";
    case "generating":
      return "Atlas is still generating this creative. It will be ready shortly.";
    case "needs-review":
      return "Approve this creative or queue it for publishing.";
    case "approved":
      return "Approved — queue it for publishing or keep tweaking.";
    case "queued":
      return "This creative is already queued for publishing.";
  }
}

type ApprovalPanelProps = {
  item: CreativeItem | null;
  feedback: string | null;
  onApprove: () => void;
  onRegenerate: () => void;
  onGenerateVariants: () => void;
  onQueue: () => void;
};

export function ApprovalPanel({
  item,
  feedback,
  onApprove,
  onRegenerate,
  onGenerateVariants,
  onQueue,
}: ApprovalPanelProps) {
  const reviewable =
    item?.status === "needs-review" || item?.status === "approved";
  const approvable = item?.status === "needs-review";
  const queueable =
    item?.status === "needs-review" || item?.status === "approved";

  return (
    <section className="rounded-xl border border-border bg-card p-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          {item && (
            <span className="relative size-10 shrink-0 overflow-hidden rounded-lg border bg-muted">
              <ProductImage src={item.imageUrl} alt={item.productName} />
            </span>
          )}
          <div className="min-w-0">
            {item ? (
              <>
                <div className="flex min-w-0 items-center gap-2">
                  <p className="truncate text-sm font-semibold tracking-tight">
                    {item.productName}
                  </p>
                  <ContentStatusBadge status={item.status} />
                </div>
                <p className="truncate text-xs text-muted-foreground">
                  {getHint(item)}
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">{getHint(item)}</p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onRegenerate}
            disabled={!reviewable}
          >
            <RefreshCw data-icon="inline-start" className="size-4" />
            Regenerate
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={onGenerateVariants}
            disabled={!reviewable}
          >
            <CopyPlus data-icon="inline-start" className="size-4" />
            Generate Variants
          </Button>
          <Button type="button" onClick={onApprove} disabled={!approvable}>
            <CheckCircle2 data-icon="inline-start" className="size-4" />
            Approve
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={onQueue}
            disabled={!queueable}
          >
            <Send data-icon="inline-start" className="size-4" />
            Queue for Publishing
          </Button>
        </div>
      </div>
      {feedback && (
        <p className="mt-3 text-xs font-medium text-primary">{feedback}</p>
      )}
    </section>
  );
}
