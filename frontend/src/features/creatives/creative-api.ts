import { makeHeadline, variantForTemplate } from "./creative-utils";
import type {
  CreativeItem,
  CreativePriority,
  CreativeStatus,
  CreativeProperties,
  TemplateId,
  VariantId,
} from "./types";

export type CreativeWorkflowRow = {
  research_product_id: number;
  product_name: string;
  category: string;
  image_url: string | null;
  price: number | null;
  rating: number | null;
  review_count: number | null;
  asin: string | null;
  ai_content_id: number | null;
  pinterest_title: string | null;
  pinterest_description: string | null;
  ai_score: number | null;
  ai_status: string | null;
  validation_status: string | null;
  creative_id: number | null;
  template_name: string | null;
  creative_headline: string | null;
  creative_image_path: string | null;
  creative_status: string | null;
  creative_error: string | null;
  creative_created_at: string | null;
  selected_template: string | null;
  selected_variant: string | null;
  creative_properties: string | null;
};

const DEFAULT_CTA = "Shop on Amazon";

type PersistedProperties = Partial<
  Pick<CreativeProperties, "cta" | "brand" | "logoPosition" | "overlayStyle">
>;

function decodeProperties(raw: string | null): PersistedProperties {
  if (!raw) return {};
  try {
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return {};
    return parsed as PersistedProperties;
  } catch {
    return {};
  }
}

function restoreTemplate(row: CreativeWorkflowRow): TemplateId {
  const candidates: TemplateId[] = [
    "minimal",
    "modern",
    "luxury",
    "lifestyle",
    "bold",
  ];
  if (
    row.selected_template !== null &&
    candidates.includes(row.selected_template as TemplateId)
  ) {
    return row.selected_template as TemplateId;
  }
  return "minimal";
}

function restoreVariant(
  row: CreativeWorkflowRow,
  templateId: TemplateId,
): VariantId {
  const candidates: VariantId[] = ["a", "b", "c", "d"];
  if (
    row.selected_variant !== null &&
    candidates.includes(row.selected_variant as VariantId)
  ) {
    return row.selected_variant as VariantId;
  }
  return variantForTemplate(templateId) ?? "a";
}

export function mapCreative(row: CreativeWorkflowRow): CreativeItem {
  const templateId = restoreTemplate(row);
  const selectedVariant = restoreVariant(row, templateId);
  const persisted = decodeProperties(row.creative_properties);

  return {
    id: String(row.research_product_id),
    productName: row.product_name,
    category: row.category,
    imageUrl: row.image_url ?? "",
    priority: derivePriority(row),
    status: deriveStatus(row),
    selectedVariant,
    templateId,
    properties: {
      headline:
        row.creative_headline ??
        row.pinterest_title ??
        makeHeadline(row.product_name),
      cta: persisted.cta ?? DEFAULT_CTA,
      brand: persisted.brand ?? "Atlas",
      logoPosition: persisted.logoPosition ?? "top-left",
      overlayStyle: persisted.overlayStyle ?? "dark",
    },
  };
}

function deriveStatus(row: CreativeWorkflowRow): CreativeStatus {
  if (row.creative_status === "APPROVED") return "approved";
  if (row.creative_status === "QUEUED") return "queued";
  if (row.creative_id !== null && row.creative_status === "FAILED") {
    return "waiting";
  }
  if (row.creative_id !== null) return "needs-review";
  return "waiting";
}

function derivePriority(row: CreativeWorkflowRow): CreativePriority {
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

export type CreativeAction = {
  success: boolean;
  creative_id: number | null;
  content?: CreativeWorkflowRow | null;
};

export type CreativePresentationPayload = {
  selected_template: string;
  selected_variant: string;
  headline: string;
  cta: string;
  brand: string;
  logo_position: string;
  overlay_style: string;
};

export function buildPresentationPayload(
  item: CreativeItem,
): CreativePresentationPayload {
  return {
    selected_template: item.templateId,
    selected_variant: item.selectedVariant,
    headline: item.properties.headline,
    cta: item.properties.cta,
    brand: item.properties.brand,
    logo_position: item.properties.logoPosition,
    overlay_style: item.properties.overlayStyle,
  };
}

export async function fetchCreatives(): Promise<CreativeItem[]> {
  const response = await fetch("/api/creatives");
  if (!response.ok) {
    throw new Error(`Failed to load creatives (${response.status})`);
  }
  const rows: CreativeWorkflowRow[] = await response.json();
  return rows.map(mapCreative);
}

export async function generateCreative(
  researchProductId: number,
  presentation?: CreativePresentationPayload,
): Promise<CreativeAction> {
  const response = await fetch("/api/creatives/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      research_product_id: researchProductId,
      ...(presentation ? { presentation } : {}),
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to generate creative (${response.status})`);
  }
  return (await response.json()) as CreativeAction;
}

export async function approveCreative(
  researchProductId: number,
  presentation?: CreativePresentationPayload,
): Promise<CreativeAction> {
  const response = await fetch("/api/creatives/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      research_product_id: researchProductId,
      ...(presentation ? { presentation } : {}),
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to approve creative (${response.status})`);
  }
  return (await response.json()) as CreativeAction;
}

export async function saveCreative(
  researchProductId: number,
  presentation: CreativePresentationPayload,
): Promise<CreativeAction> {
  const response = await fetch("/api/creatives/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      research_product_id: researchProductId,
      presentation,
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to save creative (${response.status})`);
  }
  return (await response.json()) as CreativeAction;
}

export async function reopenCreative(
  researchProductId: number,
): Promise<CreativeAction> {
  const response = await fetch("/api/creatives/reopen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ research_product_id: researchProductId }),
  });
  if (!response.ok) {
    throw new Error(`Failed to return creative to review (${response.status})`);
  }
  return (await response.json()) as CreativeAction;
}
