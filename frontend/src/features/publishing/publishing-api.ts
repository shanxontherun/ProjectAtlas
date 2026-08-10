import { makeHeadline } from "@/features/creatives/creative-utils";
import type {
  CreativeProperties,
  TemplateId,
} from "@/features/creatives/types";
import type {
  PinterestBoard,
  Publication,
  PublishItem,
  PublishPriority,
} from "./types";

export type PublishingSummary = {
  ready: number;
  scheduled: number;
  published: number;
  failed: number;
  boards: number;
};

export type PinterestAccountRow = {
  account_id: number;
  account_name: string;
  username: string;
  niche_slug: string;
  daily_limit: number;
  status: string;
  is_seed?: number;
};

export type PinterestBoardRow = {
  board_id: number;
  account_id: number;
  board_name: string;
  category_slug: string;
  status: string;
  pin_count: number;
  follower_count: number;
};

export type PublishingRow = {
  pin_id: number;
  ai_content_id: number;
  account_id: number;
  board_id: number;
  affiliate_url: string | null;
  image_url: string | null;
  publish_order: number;
  queue_status: string;
  scheduled_at: string | null;
  published_at: string | null;
  last_error: string | null;
  queued_at: string;

  research_product_id: number;
  product_name: string;
  category: string;
  price: number | null;
  rating: number | null;
  asin: string | null;

  ai_score: number | null;
  pinterest_title: string | null;
  pinterest_description: string | null;

  creative_id: number | null;
  creative_headline: string | null;
  selected_template: string | null;
  selected_variant: string | null;
  properties_json: string | null;
  creative_image_path: string | null;

  account_name: string;
  username: string;
  niche_slug: string;

  board_name: string;
  board_category_slug: string;
  pin_count: number;
  follower_count: number;
};

export type PublishingData = {
  queue: PublishingRow[];
  history: PublishingRow[];
  summary: PublishingSummary;
  accounts: PinterestAccountRow[];
  boards: PinterestBoardRow[];
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

function restoreTemplate(row: PublishingRow): TemplateId {
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

export function creativeImageUrl(row: PublishingRow): string {
  if (row.creative_id !== null) {
    return `/api/publishing/download/${row.creative_id}`;
  }
  return row.image_url ?? "";
}

function derivePriority(row: PublishingRow): PublishPriority {
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

export function mapPublishItem(row: PublishingRow): PublishItem {
  const templateId = restoreTemplate(row);
  const persisted = decodeProperties(row.properties_json);

  return {
    id: String(row.pin_id),
    productName: row.product_name,
    category: row.category,
    imageUrl: creativeImageUrl(row),
    priority: derivePriority(row),
    status: row.queue_status === "READY" ? "scheduled" : "queued",
    boardId: String(row.board_id),
    boardName: row.board_name,
    scheduledAt: row.scheduled_at,
    templateId,
    creativeId: row.creative_id,
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

export function mapPublication(row: PublishingRow): Publication {
  const eventAt =
    row.published_at ?? row.scheduled_at ?? row.queued_at;

  return {
    id: String(row.pin_id),
    productName: row.product_name,
    category: row.category,
    imageUrl: creativeImageUrl(row),
    boardName: row.board_name,
    status: mapPublicationStatus(row.queue_status),
    eventAt,
  };
}

function mapPublicationStatus(
  queueStatus: string,
): Publication["status"] {
  if (queueStatus === "PUBLISHED") return "published";
  if (queueStatus === "FAILED") return "failed";
  if (queueStatus === "CANCELLED") return "cancelled";
  return "scheduled";
}

export function mapBoard(row: PinterestBoardRow): PinterestBoard {
  return {
    id: String(row.board_id),
    name: row.board_name,
    description: row.category_slug,
    pinCount: row.pin_count,
    followerCount: row.follower_count,
  };
}

export type PublishingAction = {
  success: boolean;
  pin_id: number | null;
  content?: PublishingRow | null;
};

export async function fetchPublishing(): Promise<PublishingData> {
  const response = await fetch("/api/publishing");
  if (!response.ok) {
    throw new Error(`Failed to load publishing data (${response.status})`);
  }
  return (await response.json()) as PublishingData;
}

async function postAction(
  path: string,
  body: Record<string, unknown>,
): Promise<PublishingAction> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const message = await response.text();
    const detail = parseErrorDetail(message);
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return (await response.json()) as PublishingAction;
}

function parseErrorDetail(raw: string): string | null {
  if (!raw) return null;
  try {
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed === "object" && parsed !== null) {
      const detail = (parsed as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
    }
  } catch {
    // not JSON; fall through to raw text
  }
  return raw || null;
}

export async function queueCreative(
  researchProductId: number,
): Promise<PublishingAction> {
  return postAction("/api/publishing/queue", {
    research_product_id: researchProductId,
  });
}

export async function removeCreative(
  researchProductId: number,
): Promise<PublishingAction> {
  return postAction("/api/publishing/remove", {
    research_product_id: researchProductId,
  });
}

export async function schedulePin(
  pinId: number,
  scheduledAt: string,
): Promise<PublishingAction> {
  return postAction("/api/publishing/schedule", {
    pin_id: pinId,
    scheduled_at: scheduledAt,
  });
}

export async function publishNow(pinId: number): Promise<PublishingAction> {
  return postAction("/api/publishing/publish-now", {
    pin_id: pinId,
  });
}

export async function updatePinBoard(
  pinId: number,
  accountId: number,
  boardId: number,
): Promise<PublishingAction> {
  return postAction("/api/publishing/board", {
    pin_id: pinId,
    account_id: accountId,
    board_id: boardId,
  });
}

export async function downloadCreative(creativeId: number) {
  const response = await fetch(`/api/publishing/download/${creativeId}`);
  if (!response.ok) {
    throw new Error(`Failed to download pin (${response.status})`);
  }
  return response;
}
