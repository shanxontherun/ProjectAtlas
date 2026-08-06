import type {
  ContentDraft,
  ContentItem,
  ContentStatusFilter,
} from "./types";

const SORT_RANK: Record<ContentItem["status"], number> = {
  "needs-review": 0,
  waiting: 1,
  generating: 2,
  approved: 3,
  queued: 4,
};

export type ContentFilters = {
  query: string;
  status: ContentStatusFilter;
};

export function filterContentItems(items: ContentItem[], filters: ContentFilters) {
  const query = filters.query.trim().toLowerCase();

  return items
    .filter((item) => filters.status === "all" || item.status === filters.status)
    .filter(
      (item) =>
        query === "" ||
        item.productName.toLowerCase().includes(query) ||
        item.category.toLowerCase().includes(query),
    )
    .sort(
      (a, b) => SORT_RANK[a.status] - SORT_RANK[b.status],
    );
}

export function getContentCounts(items: ContentItem[]) {
  const counts = {
    waiting: 0,
    generating: 0,
    needsReview: 0,
    approved: 0,
  };

  for (const item of items) {
    if (item.status === "waiting") counts.waiting += 1;
    if (item.status === "generating") counts.generating += 1;
    if (item.status === "needs-review") counts.needsReview += 1;
    if (item.status === "approved") counts.approved += 1;
  }

  return counts;
}

const CLOSERS = [
  "Save this pin for your next organizing project!",
  "Tap to shop it now on Amazon.",
  "Your space will thank you — grab yours today.",
  "Pin it now so you don't forget it later.",
];

const DETAILS = [
  "Built to last with a durable, easy-to-clean finish.",
  "Fits neatly on shelves, countertops, and in cabinets.",
  "Ships fast and arrives ready to use.",
  "Loved by shoppers for its simple, practical design.",
];

function appendSentence(text: string, sentence: string) {
  const trimmed = text.trim();
  if (!trimmed) return sentence;
  if (/[.!?]$/.test(trimmed)) return `${trimmed} ${sentence}`;
  return `${trimmed}. ${sentence}`;
}

export function shorten(text: string, max = 180) {
  const trimmed = text.trim();
  if (trimmed.length <= max) return trimmed;

  const cut = trimmed.slice(0, max);
  const lastSpace = cut.lastIndexOf(" ");
  const end = lastSpace > 60 ? lastSpace : max;

  return `${cut.slice(0, end).replace(/[.,;:\s]+$/, "")}…`;
}

export function improveDraft(draft: ContentDraft): ContentDraft {
  return {
    ...draft,
    description: appendSentence(draft.description, CLOSERS[0]),
    seoScore: Math.min(100, draft.seoScore + 8),
  };
}

export function shortenDraft(draft: ContentDraft): ContentDraft {
  return { ...draft, description: shorten(draft.description, 180) };
}

export function expandDraft(draft: ContentDraft, seed: number): ContentDraft {
  return {
    ...draft,
    description: appendSentence(draft.description, DETAILS[seed % DETAILS.length]),
  };
}
