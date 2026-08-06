"use client";

import type { Product } from "./types";
import { ProductCard } from "./product-card";

type ProductGridProps = {
  products: Product[];
  onSelect: (product: Product) => void;
};

export function ProductGrid({ products, onSelect }: ProductGridProps) {
  return (
    <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {products.map((product) => (
        <li key={product.id}>
          <ProductCard product={product} onSelect={onSelect} />
        </li>
      ))}
    </ul>
  );
}
