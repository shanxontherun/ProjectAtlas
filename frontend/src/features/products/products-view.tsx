"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { MOCK_PRODUCTS } from "./mock-data";
import {
  filterAndSortProducts,
  getCategories,
  type SortKey,
} from "./product-utils";
import { ProductDrawer } from "./product-drawer";
import { ProductEmptyState } from "./product-empty-state";
import { ProductGrid } from "./product-grid";
import { ProductList } from "./product-list";
import { ProductSkeleton } from "./product-skeleton";
import {
  ProductToolbar,
  type ProductsViewMode,
} from "./product-toolbar";
import type { Product } from "./types";

const DEFAULT_FILTERS = {
  query: "",
  category: "all",
  stage: "all",
  sort: "recommended" as SortKey,
};

export function ProductsView() {
  const [search, setSearch] = useState(DEFAULT_FILTERS.query);
  const [category, setCategory] = useState(DEFAULT_FILTERS.category);
  const [stage, setStage] = useState(DEFAULT_FILTERS.stage);
  const [sort, setSort] = useState<SortKey>(DEFAULT_FILTERS.sort);
  const [view, setView] = useState<ProductsViewMode>("grid");
  const [selected, setSelected] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => setLoading(false), 650);
    return () => window.clearTimeout(timer);
  }, []);

  const categories = useMemo(() => getCategories(MOCK_PRODUCTS), []);
  const deferredQuery = useDeferredValue(search);

  const products = useMemo(
    () =>
      filterAndSortProducts(MOCK_PRODUCTS, {
        query: deferredQuery,
        category,
        stage,
        sort,
      }),
    [deferredQuery, category, stage, sort],
  );

  const hasActiveFilters =
    search.trim() !== "" ||
    category !== DEFAULT_FILTERS.category ||
    stage !== DEFAULT_FILTERS.stage ||
    sort !== DEFAULT_FILTERS.sort;

  function clearFilters() {
    setSearch(DEFAULT_FILTERS.query);
    setCategory(DEFAULT_FILTERS.category);
    setStage(DEFAULT_FILTERS.stage);
    setSort(DEFAULT_FILTERS.sort);
  }

  return (
    <div className="flex flex-col gap-6">
      <ProductToolbar
        search={search}
        onSearchChange={setSearch}
        categories={categories}
        category={category}
        onCategoryChange={setCategory}
        stage={stage}
        onStageChange={setStage}
        sort={sort}
        onSortChange={setSort}
        view={view}
        onViewChange={setView}
      />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <ProductSkeleton key={index} />
          ))}
        </div>
      ) : products.length === 0 ? (
        <ProductEmptyState
          variant={hasActiveFilters ? "no-results" : "no-products"}
          onClearFilters={hasActiveFilters ? clearFilters : undefined}
        />
      ) : view === "grid" ? (
        <ProductGrid products={products} onSelect={setSelected} />
      ) : (
        <ProductList products={products} onSelect={setSelected} />
      )}

      {!loading && products.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Showing {products.length} of {MOCK_PRODUCTS.length} products
        </p>
      )}

      <ProductDrawer
        product={selected}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
