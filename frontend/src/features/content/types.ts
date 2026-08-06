export type ContentStatus =
  | "waiting"
  | "generating"
  | "needs-review"
  | "approved"
  | "queued";

export type ContentPriority = "high" | "medium" | "low";

export type ContentDraft = {
  title: string;
  description: string;
  hashtags: string;
  cta: string;
  seoScore: number;
};

export type ContentItem = {
  id: string;
  productName: string;
  category: string;
  imageUrl: string;
  priority: ContentPriority;
  status: ContentStatus;
  hasChanges: boolean;
  draft: ContentDraft | null;
};

export type ContentStatusFilter = ContentStatus | "all";

export type EditorAction =
  | "copy"
  | "improve"
  | "regenerate"
  | "shorten"
  | "expand"
  | "reset";

export const TITLE_LIMIT = 100;
export const DESCRIPTION_LIMIT = 500;
