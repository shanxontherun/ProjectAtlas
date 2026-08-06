import type { Product, ProductHealth } from "./types";

export type ResearchProductRow = {
  research_product_id: number;
  job_id: number;
  category: string;
  product_name: string;
  product_url: string;
  source: string;
  price: number | null;
  currency: string;
  rating: number | null;
  review_count: number | null;
  image_url: string | null;
  ai_summary: string | null;
  status: string;
  created_at: string;
  asin: string | null;
};

const STATUS_TO_PROGRESS: Record<string, number> = {
  NEW: 25,
  GENERATED: 50,
  QUEUED: 75,
  PUBLISHED: 100,
  FAILED: 25,
};

const STATUS_TO_HEALTH: Record<string, ProductHealth> = {
  NEW: "needs-attention",
  GENERATED: "ready",
  QUEUED: "ready",
  PUBLISHED: "ready",
  FAILED: "blocked",
};

export function mapResearchProduct(row: ResearchProductRow): Product {
  return {
    id: String(row.research_product_id),
    name: row.product_name,
    category: row.category,
    price: row.price ?? 0,
    currency: row.currency || "USD",
    rating: row.rating ?? 0,
    reviewCount: row.review_count ?? 0,
    asin: row.asin ?? "",
    source: row.source || "Amazon",
    imageUrl: row.image_url ?? "",
    description: row.ai_summary ?? "",
    progress: STATUS_TO_PROGRESS[row.status] ?? 0,
    health: STATUS_TO_HEALTH[row.status] ?? "needs-attention",
    addedAt: row.created_at.slice(0, 10),
  };
}

export async function fetchProducts(): Promise<Product[]> {
  const response = await fetch("/api/research-products");
  if (!response.ok) {
    throw new Error(`Failed to load products (${response.status})`);
  }
  const rows: ResearchProductRow[] = await response.json();
  return rows.map(mapResearchProduct);
}
