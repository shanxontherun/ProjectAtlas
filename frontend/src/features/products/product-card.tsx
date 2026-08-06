"use client";

import { ArrowRight, Star } from "lucide-react";
import { HealthBadge } from "./health-badge";
import { ProgressBar } from "./progress-bar";
import { ProductImage } from "./product-image";
import { getCurrentStage, type Product } from "./types";
import { formatCompactNumber, formatCurrency } from "./format";

type ProductCardProps = {
  product: Product;
  onSelect: (product: Product) => void;
};

export function ProductCard({ product, onSelect }: ProductCardProps) {
  const stage = getCurrentStage(product.progress);

  return (
    <button
      type="button"
      onClick={() => onSelect(product)}
      aria-label={`View details for ${product.name}`}
      className="group relative flex flex-col overflow-hidden rounded-xl border border-border bg-card text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-border/80 hover:shadow-lg hover:shadow-black/[0.04] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-muted">
        <ProductImage
          src={product.imageUrl}
          alt={product.name}
          className="transition-transform duration-300 ease-out group-hover:scale-[1.03]"
        />
        <div className="absolute right-3 top-3">
          <HealthBadge health={product.health} />
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">{product.category}</span>
          <h3 className="line-clamp-2 text-sm font-medium leading-snug">
            {product.name}
          </h3>
        </div>

        <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-muted-foreground">
          <Star
            className="size-3.5 fill-amber-500/90 text-amber-500/90 dark:fill-amber-400/90 dark:text-amber-400/90"
            aria-hidden="true"
          />
          <span className="font-medium text-foreground">
            {product.rating.toFixed(1)}
          </span>
          <span aria-hidden="true">·</span>
          <span>{formatCompactNumber(product.reviewCount)} reviews</span>
          <span aria-hidden="true">·</span>
          <span className="font-medium text-foreground">
            {formatCurrency(product.price, product.currency)}
          </span>
        </div>

        <div className="mt-auto flex flex-col gap-1.5 pt-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">{stage.label}</span>
            <span className="tabular-nums text-muted-foreground">
              {product.progress}%
            </span>
          </div>
          <ProgressBar value={product.progress} showValue={false} />
        </div>

        <div className="flex items-center gap-1 pt-0.5 text-xs font-medium text-primary">
          View details
          <ArrowRight className="size-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
        </div>
      </div>
    </button>
  );
}
