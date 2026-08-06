import { getCurrentStage, type Product } from "./types";

export type SortKey =
  | "recommended"
  | "name"
  | "price-asc"
  | "price-desc"
  | "rating"
  | "progress";

export type ProductFilters = {
  query: string;
  category: string;
  stage: string;
  sort: SortKey;
};

export function getCategories(products: Product[]) {
  return [...new Set(products.map((product) => product.category))];
}

export function filterAndSortProducts(
  products: Product[],
  filters: ProductFilters,
) {
  const query = filters.query.trim().toLowerCase();

  const filtered = products.filter((product) => {
    const matchesQuery =
      query.length === 0 ||
      product.name.toLowerCase().includes(query) ||
      product.category.toLowerCase().includes(query);
    const matchesCategory =
      filters.category === "all" || product.category === filters.category;
    const matchesStage =
      filters.stage === "all" ||
      getCurrentStage(product.progress).key === filters.stage;

    return matchesQuery && matchesCategory && matchesStage;
  });

  const sorted = [...filtered];
  switch (filters.sort) {
    case "name":
      sorted.sort((a, b) => a.name.localeCompare(b.name));
      break;
    case "price-asc":
      sorted.sort((a, b) => a.price - b.price);
      break;
    case "price-desc":
      sorted.sort((a, b) => b.price - a.price);
      break;
    case "rating":
      sorted.sort((a, b) => b.rating - a.rating);
      break;
    case "progress":
      sorted.sort((a, b) => b.progress - a.progress);
      break;
    default:
      break;
  }

  return sorted;
}
