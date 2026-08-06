export type ProductHealth = "ready" | "needs-attention" | "blocked";

export type Product = {
  id: string;
  name: string;
  category: string;
  price: number;
  currency: string;
  rating: number;
  reviewCount: number;
  asin: string;
  source: string;
  imageUrl: string;
  description: string;
  progress: number;
  health: ProductHealth;
  addedAt: string;
};

export const WORKFLOW_STAGES = [
  { key: "imported", label: "Imported", min: 0 },
  { key: "research", label: "Research Complete", min: 25 },
  { key: "ai", label: "AI Ready", min: 50 },
  { key: "creative", label: "Creative Ready", min: 75 },
  { key: "published", label: "Published", min: 100 },
] as const;

export type WorkflowStageKey = (typeof WORKFLOW_STAGES)[number]["key"];

export function getCurrentStage(progress: number) {
  const clamped = Math.min(100, Math.max(0, progress));
  return (
    [...WORKFLOW_STAGES].findLast((stage) => clamped >= stage.min) ??
    WORKFLOW_STAGES[0]
  );
}

export const HEALTH_META: Record<
  ProductHealth,
  { label: string; dotClass: string; badgeClass: string }
> = {
  ready: {
    label: "Ready",
    dotClass: "bg-emerald-500",
    badgeClass:
      "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  },
  "needs-attention": {
    label: "Needs Attention",
    dotClass: "bg-amber-500",
    badgeClass:
      "border-amber-500/25 bg-amber-500/10 text-amber-600 dark:text-amber-400",
  },
  blocked: {
    label: "Blocked",
    dotClass: "bg-red-500",
    badgeClass:
      "border-red-500/25 bg-red-500/10 text-red-600 dark:text-red-400",
  },
};
