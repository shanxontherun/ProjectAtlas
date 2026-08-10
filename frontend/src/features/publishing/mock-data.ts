import { MOCK_PRODUCTS } from "@/features/products/mock-data";
import {
  DEFAULT_CTA,
  makeHeadline,
} from "@/features/creatives/creative-utils";
import type { CreativeProperties, TemplateId } from "@/features/creatives/types";
import type {
  PinterestBoard,
  Publication,
  PublishItem,
  PublishPriority,
} from "./types";

function product(name: string) {
  const found = MOCK_PRODUCTS.find((item) => item.name === name);
  if (!found) throw new Error(`Unknown mock product: ${name}`);
  return found;
}

function plusHours(hours: number) {
  return new Date(Date.now() + hours * 3_600_000).toISOString();
}

function tomorrowAt(hour: number, minute = 0) {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  date.setHours(hour, minute, 0, 0);
  return date.toISOString();
}

export const MOCK_BOARDS: PinterestBoard[] = [
  {
    id: "board_home_essentials",
    name: "Home Essentials",
    description: "Curated picks for everyday living.",
    pinCount: 1240,
    followerCount: 48200,
  },
  {
    id: "board_kitchen_org",
    name: "Kitchen Organization",
    description: "Shelves, bins, and tidy counters.",
    pinCount: 890,
    followerCount: 32100,
  },
  {
    id: "board_laundry",
    name: "Laundry Hacks",
    description: "Faster, tidier laundry routines.",
    pinCount: 560,
    followerCount: 21400,
  },
  {
    id: "board_bathroom",
    name: "Bathroom Ideas",
    description: "Small-space bathroom upgrades.",
    pinCount: 720,
    followerCount: 27600,
  },
  {
    id: "board_amazon_finds",
    name: "Amazon Home Finds",
    description: "Affordable finds under $50.",
    pinCount: 1520,
    followerCount: 91400,
  },
];

export const BOARD_BY_ID = Object.fromEntries(
  MOCK_BOARDS.map((board) => [board.id, board]),
) as Record<string, PinterestBoard>;

const QUEUE_PLANS: {
  productName: string;
  priority: PublishPriority;
  status: PublishItem["status"];
  boardId: string;
  templateId: TemplateId;
  overlayStyle: CreativeProperties["overlayStyle"];
  scheduledAt?: string;
}[] = [
  {
    productName: "Expandable Kitchen Storage Basket",
    priority: "high",
    status: "queued",
    boardId: "board_kitchen_org",
    templateId: "minimal",
    overlayStyle: "dark",
  },
  {
    productName: "Foldable Laundry Bag",
    priority: "high",
    status: "queued",
    boardId: "board_laundry",
    templateId: "bold",
    overlayStyle: "gradient",
  },
  {
    productName: "Pantry Organizer Bins Set of 4",
    priority: "medium",
    status: "queued",
    boardId: "board_kitchen_org",
    templateId: "luxury",
    overlayStyle: "dark",
  },
  {
    productName: "Under-Sink Organizer",
    priority: "medium",
    status: "scheduled",
    boardId: "board_bathroom",
    templateId: "lifestyle",
    overlayStyle: "light",
    scheduledAt: plusHours(3),
  },
  {
    productName: "Stackable Pantry Storage Jars",
    priority: "low",
    status: "queued",
    boardId: "board_amazon_finds",
    templateId: "minimal",
    overlayStyle: "dark",
  },
];

function buildPublishItem(
  plan: (typeof QUEUE_PLANS)[number],
  index: number,
): PublishItem {
  const prod = product(plan.productName);

  return {
    id: `publish_queue_${index}`,
    productName: prod.name,
    category: prod.category,
    imageUrl: prod.imageUrl,
    priority: plan.priority,
    status: plan.status,
    boardId: plan.boardId,
    boardName: plan.boardId ? (BOARD_BY_ID[plan.boardId]?.name ?? null) : null,
    scheduledAt: plan.scheduledAt ?? null,
    templateId: plan.templateId,
    creativeId: null,
    properties: {
      headline: makeHeadline(prod.name),
      cta: DEFAULT_CTA,
      brand: "Atlas",
      logoPosition: "top-left",
      overlayStyle: plan.overlayStyle,
    },
  };
}

export const MOCK_PUBLISH_QUEUE: PublishItem[] = QUEUE_PLANS.map(
  (plan, index) => buildPublishItem(plan, index),
);

export const MOCK_PUBLICATIONS: Publication[] = [
  {
    id: "pub_1",
    productName: "Closet Shelf Organizer",
    category: "Home Storage",
    imageUrl: product("Closet Shelf Organizer").imageUrl,
    boardName: "Home Essentials",
    status: "published",
    eventAt: plusHours(-2),
  },
  {
    id: "pub_2",
    productName: "Over-Door Shoe Rack",
    category: "Home Storage",
    imageUrl: product("Over-Door Shoe Rack").imageUrl,
    boardName: "Laundry Hacks",
    status: "published",
    eventAt: plusHours(-5),
  },
  {
    id: "pub_3",
    productName: "Foldable Laundry Bag",
    category: "Home Storage",
    imageUrl: product("Foldable Laundry Bag").imageUrl,
    boardName: "Amazon Home Finds",
    status: "published",
    eventAt: plusHours(-26),
  },
  {
    id: "pub_4",
    productName: "Bamboo Bathroom Shelf",
    category: "Home Storage",
    imageUrl: product("Bamboo Bathroom Shelf").imageUrl,
    boardName: "Bathroom Ideas",
    status: "scheduled",
    eventAt: tomorrowAt(9),
  },
  {
    id: "pub_5",
    productName: "Hanging Closet Organizer",
    category: "Home Storage",
    imageUrl: product("Hanging Closet Organizer").imageUrl,
    boardName: "Home Essentials",
    status: "failed",
    eventAt: plusHours(-30),
  },
];
