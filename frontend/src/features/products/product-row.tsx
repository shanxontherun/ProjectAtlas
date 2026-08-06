"use client";

import { ChevronRight, Star } from "lucide-react";
import { HealthBadge } from "./health-badge";
import { ProgressBar } from "./progress-bar";
import { ProductImage } from "./product-image";
import type { Product } from "./types";
import { formatCompactNumber, formatCurrency } from "./format";

type ProductRowProps = {
  product: Product;
  onSelect: (product: Product) => void;
};

export function ProductRow({ product, onSelect }: ProductRowProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(product)}
      aria-label={`View details for ${product.name}`}
      className="group grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-border bg-card p-3 text-left transition-all duration-200 hover:border-border/80 hover:shadow-sm focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 md:grid-cols-[auto_minmax(0,1fr)_auto_auto_auto_minmax(0,150px)_auto]"
    >
      <div className="relative size-14 shrink-0 overflow-hidden rounded-lg bg-muted md:size-12">
        <ProductImage
          src={product.imageUrl}
          alt={product.name}
          sizes="64px"
          className="transition-transform duration-300 ease-out group-hover:scale-105"
        />
      </div>

      <div className="min-w-0">
        <h3 className="truncate text-sm font-medium">{product.name}</h3>
        <p className="truncate text-xs text-muted-foreground">
          {product.category}
        </p>
        <div className="mt-2 md:hidden">
          <ProgressBar value={product.progress} showValue={false} />
        </div>
      </div>

      <div className="hidden items-center gap-1.5 text-xs text-muted-foreground md:flex">
        <Star
          className="size-3.5 fill-amber-500/90 text-amber-500/90 dark:fill-amber-400/90 dark:text-amber-400/90"
          aria-hidden="true"
        />
        <span className="font-medium tabular-nums text-foreground">
          {product.rating.toFixed(1)}
        </span>
        <span aria-hidden="true">·</span>
        <span>{formatCompactNumber(product.reviewCount)}</span>
      </div>

      <div className="hidden text-sm font-medium tabular-nums md:block">
        {formatCurrency(product.price, product.currency)}
      </div>

      <div className="hidden md:block">
        <HealthBadge health={product.health} />
      </div>

      <div className="hidden min-w-0 md:block">
        <div className="flex items-center justify-between gap-2 text-xs">
          <span className="truncate text-muted-foreground">Workflow</span>
          <span className="font-medium tabular-nums text-foreground">
            {product.progress}%
          </span>
        </div>
        <div className="mt-1.5">
          <ProgressBar value={product.progress} showValue={false} />
        </div>
      </div>

      <div className="flex flex-col items-end gap-2">
        <HealthBadge health={product.health} className="md:hidden" />
        <ChevronRight className="size-4 text-muted-foreground transition-transform duration-200 group-hover:translate-x-0.5" />
      </div>
    </button>
  );
}
