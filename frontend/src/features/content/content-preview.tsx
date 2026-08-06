"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ProductImage } from "@/features/products/product-image";
import type { ContentItem } from "./types";

type ContentPreviewProps = {
  item: ContentItem | null;
  onClose: () => void;
};

export function ContentPreview({ item, onClose }: ContentPreviewProps) {
  const draft = item?.draft;

  return (
    <Dialog open={item !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Pin preview</DialogTitle>
          <DialogDescription>
            How this content will appear on Pinterest.
          </DialogDescription>
        </DialogHeader>

        {item && (
          <div className="mx-auto w-60">
            <div className="relative aspect-[2/3] overflow-hidden rounded-xl border bg-muted">
              <ProductImage src={item.imageUrl} alt={item.productName} />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 via-black/40 to-transparent p-3">
                <p className="line-clamp-3 text-sm leading-snug font-semibold text-white">
                  {draft?.title ?? item.productName}
                </p>
              </div>
            </div>

            <div className="mt-3 space-y-2 text-sm">
              <p className="text-xs text-muted-foreground">{item.productName}</p>
              {draft && (
                <>
                  <p className="line-clamp-4 text-sm leading-relaxed">
                    {draft.description}
                  </p>
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    {draft.hashtags}
                  </p>
                  <p className="text-xs font-medium text-primary">{draft.cta}</p>
                </>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
