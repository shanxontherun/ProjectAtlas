"use client";

import { cn } from "@/lib/utils";
import { CREATIVE_VARIANTS, TEMPLATE_BY_ID } from "./mock-data";
import { CreativePin } from "./creative-preview";
import type { CreativeItem, VariantId } from "./types";

type VariantGalleryProps = {
  item: CreativeItem | null;
  onSelect: (variantId: VariantId) => void;
};

export function VariantGallery({ item, onSelect }: VariantGalleryProps) {
  const locked =
    item !== null &&
    (item.status === "approved" || item.status === "queued");

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="flex items-center justify-between gap-2">
        <div className="space-y-0.5">
          <h2 className="text-sm font-semibold tracking-tight">Variants</h2>
          <p className="text-xs text-muted-foreground">
            Compare generated options for this creative.
          </p>
        </div>
        <span className="text-xs tabular-nums text-muted-foreground">
          {CREATIVE_VARIANTS.length} variants
        </span>
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {CREATIVE_VARIANTS.map((variant) => {
          const active =
            item?.selectedVariant === variant.id &&
            item.templateId === variant.templateId;
          const template = TEMPLATE_BY_ID[variant.templateId];

          return (
            <button
              key={variant.id}
              type="button"
              disabled={!item || locked}
              onClick={() => onSelect(variant.id)}
              aria-pressed={active}
              className={cn(
                "group flex flex-col gap-2 rounded-lg border p-2 text-left outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50",
                active
                  ? "border-primary bg-muted/50"
                  : "border-border hover:bg-muted/40",
              )}
            >
              {item ? (
                <CreativePin
                  imageUrl={item.imageUrl}
                  productName={item.productName}
                  category={item.category}
                  template={template}
                  properties={item.properties}
                  className="rounded-md"
                />
              ) : (
                <div
                  className="aspect-[2/3] w-full rounded-md bg-muted"
                  aria-hidden="true"
                />
              )}
              <span className="flex flex-col">
                <span
                  className={cn(
                    "text-xs font-medium",
                    active ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  {variant.label}
                </span>
                <span className="text-[0.7rem] text-muted-foreground">
                  {variant.style}
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
