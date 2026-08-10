import type {
  CreativeProperties,
  TemplateId,
} from "@/features/creatives/types";

export type PublishPriority = "high" | "medium" | "low";

export type PublishQueueStatus = "queued" | "scheduled";

export type PublicationStatus = "published" | "scheduled" | "failed" | "cancelled";

export type PinterestBoard = {
  id: string;
  name: string;
  description: string;
  pinCount: number;
  followerCount: number;
};

export type PublishItem = {
  id: string;
  productName: string;
  category: string;
  imageUrl: string;
  priority: PublishPriority;
  status: PublishQueueStatus;
  boardId: string | null;
  boardName: string | null;
  scheduledAt: string | null;
  templateId: TemplateId;
  creativeId: number | null;
  properties: CreativeProperties;
};

export type Publication = {
  id: string;
  productName: string;
  category: string;
  imageUrl: string;
  boardName: string;
  status: PublicationStatus;
  eventAt: string;
};

export type PublishTimingMode = "now" | "schedule";
