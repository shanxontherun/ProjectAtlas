"use client";

import type { Product } from "./types";
import { ProductRow } from "./product-row";

type ProductListProps = {
  products: Product[];
  onSelect: (product: Product) => void;
};

export function ProductList({ products, onSelect }: ProductListProps) {
  return (
    <ul className="flex flex-col gap-3">
      {products.map((product) => (
        <li key={product.id}>
          <ProductRow product={product} onSelect={onSelect} />
        </li>
      ))}
    </ul>
  );
}
