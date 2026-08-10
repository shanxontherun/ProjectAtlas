"use client";

import { LayoutGrid } from "lucide-react";
import { SectionCard } from "@/features/dashboard/section-card";
import { ProductImage } from "@/features/products/product-image";
import { formatPublishTime, relativeTime } from "./publishing-utils";
import { PublishingStatusBadge } from "./publishing-status-badge";
import type { Publication } from "./types";

type PublishedHistoryProps = {
  publications: Publication[];
};

export function PublishedHistory({ publications }: PublishedHistoryProps) {

  return (
    <SectionCard
      title="Published History"
      description="Pins that have gone live, are scheduled, or need attention."
      action={
        <span className="text-xs tabular-nums text-muted-foreground">
          {publications.length} {publications.length === 1 ? "pin" : "pins"}
        </span>
      }
    >
      {publications.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed bg-muted/30 px-4 py-10 text-center">
          <p className="text-sm font-medium">No Pins published yet</p>
          <p className="max-w-[20rem] text-xs text-muted-foreground">
            Connect a Pinterest account and publish a pin for it to appear
            here.
          </p>
        </div>
      ) : (
        <ul className="flex flex-col">
          {publications.map((publication) => (
            <li
              key={publication.id}
              className="flex items-center gap-3 border-t border-border py-3 first:border-t-0 first:pt-0 last:pb-0"
            >
              <span className="relative size-10 shrink-0 overflow-hidden rounded-md border bg-muted">
                <ProductImage
                  src={publication.imageUrl}
                  alt={publication.productName}
                />
              </span>

              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium">
                  {publication.productName}
                </span>
                <span className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <LayoutGrid className="size-3" aria-hidden="true" />
                  <span className="truncate">{publication.boardName}</span>
                  <span aria-hidden="true">·</span>
                  <span>
                    {publication.status === "scheduled"
                      ? formatPublishTime(publication.eventAt)
                      : relativeTime(publication.eventAt)}
                  </span>
                </span>
              </span>

              <PublishingStatusBadge status={publication.status} />
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}
