import type {
  ContentDraft,
  ContentItem,
  ContentPriority,
  ContentStatus,
} from "./types";

export type AiContentRow = {
  research_product_id: number;
  product_name: string;
  category: string;
  image_url: string | null;
  price: number | null;
  rating: number | null;
  ai_summary: string | null;
  research_status: string;
  research_created_at: string;
  ai_content_id: number | null;
  seo_title: string | null;
  pinterest_title: string | null;
  pinterest_description: string | null;
  pinterest_keywords: string | null;
  board_name: string | null;
  instagram_caption: string | null;
  blog_summary: string | null;
  ai_score: number | null;
  content_status: string | null;
  validation_status: string | null;
  validation_error: string | null;
  content_created_at: string | null;
  content_updated_at: string | null;
};

const DEFAULT_CTA = "Shop on Amazon";

export function mapAiContent(row: AiContentRow): ContentItem {
  return {
    id: String(row.research_product_id),
    productName: row.product_name,
    category: row.category,
    imageUrl: row.image_url ?? "",
    priority: derivePriority(row),
    status: deriveStatus(row),
    hasChanges: false,
    draft: row.ai_content_id !== null ? mapDraft(row) : null,
  };
}

function mapDraft(row: AiContentRow): ContentDraft {
  return {
    title: row.pinterest_title ?? "",
    description: row.pinterest_description ?? "",
    hashtags: row.pinterest_keywords ?? "",
    cta: DEFAULT_CTA,
    seoScore: row.ai_score ?? 0,
  };
}

function deriveStatus(row: AiContentRow): ContentStatus {
  if (
    row.research_status === "QUEUED" ||
    row.research_status === "PUBLISHED"
  ) {
    return "queued";
  }
  if (row.content_status === "APPROVED") {
    return "approved";
  }
  if (row.ai_content_id !== null) {
    return "needs-review";
  }
  return "waiting";
}

function derivePriority(row: AiContentRow): ContentPriority {
  if (row.ai_score !== null) {
    if (row.ai_score >= 85) return "high";
    if (row.ai_score >= 70) return "medium";
    return "low";
  }
  if (row.rating !== null) {
    if (row.rating >= 4.5) return "high";
    if (row.rating >= 4.0) return "medium";
    return "low";
  }
  return "medium";
}

export type AiContentAction = {
  success: boolean;
  ai_content_id: number | null;
  content?: AiContentRow | null;
};

export async function fetchAiContent(): Promise<ContentItem[]> {
  const response = await fetch("/api/ai-content");
  if (!response.ok) {
    throw new Error(`Failed to load AI content (${response.status})`);
  }
  const rows: AiContentRow[] = await response.json();
  return rows.map(mapAiContent);
}

export async function generateAiContent(
  researchProductId: number,
): Promise<AiContentAction> {
  const response = await fetch("/api/ai-content/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ research_product_id: researchProductId }),
  });
  if (!response.ok) {
    throw new Error(`Failed to generate content (${response.status})`);
  }
  return (await response.json()) as AiContentAction;
}

export async function approveAiContent(
  researchProductId: number,
): Promise<AiContentAction> {
  const response = await fetch("/api/ai-content/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ research_product_id: researchProductId }),
  });
  if (!response.ok) {
    throw new Error(`Failed to approve content (${response.status})`);
  }
  return (await response.json()) as AiContentAction;
}
