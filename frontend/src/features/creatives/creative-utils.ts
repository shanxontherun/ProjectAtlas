import {
  CTA_LIMIT,
  HEADLINE_LIMIT,
} from "./types";
import type {
  CreativeItem,
  CreativeProperties,
  CreativeStatus,
  TemplateId,
  VariantId,
} from "./types";

const SORT_RANK: Record<CreativeStatus, number> = {
  "needs-review": 0,
  waiting: 1,
  generating: 2,
  approved: 3,
  queued: 4,
};

export function sortCreativeItems(items: CreativeItem[]) {
  return [...items].sort(
    (a, b) => SORT_RANK[a.status] - SORT_RANK[b.status],
  );
}

export function getCreativeCounts(items: CreativeItem[]) {
  const counts = {
    waiting: 0,
    generating: 0,
    needsReview: 0,
    approved: 0,
    queued: 0,
  };

  for (const item of items) {
    if (item.status === "waiting") counts.waiting += 1;
    if (item.status === "generating") counts.generating += 1;
    if (item.status === "needs-review") counts.needsReview += 1;
    if (item.status === "approved") counts.approved += 1;
    if (item.status === "queued") counts.queued += 1;
  }

  return counts;
}

export function makeHeadline(productName: string) {
  const overrides: Record<string, string> = {
    "Expandable Kitchen Storage Basket": "Instantly Organize Any Kitchen Space",
    "Foldable Laundry Bag": "Haul Laundry With Ease, Then Stash It Flat",
    "Pantry Organizer Bins Set of 4": "See Everything in Your Pantry at a Glance",
    "Under-Sink Organizer": "Unclutter Under Your Sink in Minutes",
    "Stackable Pantry Storage Jars": "Beautiful Pantry Jars Worth Showing Off",
    "Closet Shelf Organizer": "Double Your Closet Space Without a Rack",
    "Over-Door Shoe Rack": "Hang 12 Pairs of Shoes on the Back of a Door",
    "Bamboo Bathroom Shelf": "A Shelf That Keeps Your Bathroom Tidy",
  };

  return (
    overrides[productName] ??
    `Discover the ${productName} Your Home Needs`
  );
}

export const DEFAULT_CTA = "Shop on Amazon";

const DEFAULT_PROPERTIES: CreativeProperties = {
  headline: "",
  cta: DEFAULT_CTA,
  brand: "Atlas",
  logoPosition: "top-left",
  overlayStyle: "dark",
};

export const VARIANT_TEMPLATE_MAP: Record<VariantId, TemplateId> = {
  a: "minimal",
  b: "luxury",
  c: "lifestyle",
  d: "bold",
};

export function variantForTemplate(templateId: TemplateId) {
  const match = (
    Object.entries(VARIANT_TEMPLATE_MAP) as [VariantId, TemplateId][]
  ).find(([, template]) => template === templateId);
  return match?.[0];
}

export function buildCreativeItem(
  product: { name: string; category: string; imageUrl: string },
  overrides: {
    id?: string;
    priority: CreativeItem["priority"];
    status?: CreativeItem["status"];
    templateId?: TemplateId;
    selectedVariant?: VariantId;
    headline?: string;
    cta?: string;
    brand?: string;
    logoPosition?: CreativeProperties["logoPosition"];
    overlayStyle?: CreativeProperties["overlayStyle"];
  },
): CreativeItem {
  const templateId = overrides.templateId ?? "minimal";
  const selectedVariant = overrides.selectedVariant ?? "a";

  return {
    id: overrides.id ?? `creative_${product.name.replace(/[^a-zA-Z0-9]+/g, "_").toLowerCase()}`,
    productName: product.name,
    category: product.category,
    imageUrl: product.imageUrl,
    priority: overrides.priority,
    status: overrides.status ?? "waiting",
    selectedVariant,
    templateId,
    properties: {
      headline: overrides.headline ?? makeHeadline(product.name),
      cta: overrides.cta ?? DEFAULT_PROPERTIES.cta,
      brand: overrides.brand ?? DEFAULT_PROPERTIES.brand,
      logoPosition: overrides.logoPosition ?? DEFAULT_PROPERTIES.logoPosition,
      overlayStyle: overrides.overlayStyle ?? DEFAULT_PROPERTIES.overlayStyle,
    },
  };
}

export function nextVariant(variantId: VariantId): VariantId {
  const order: VariantId[] = ["a", "b", "c", "d"];
  const index = order.indexOf(variantId);
  return order[(index + 1) % order.length];
}

export type ReadinessEntry = {
  id: string;
  label: string;
  done: boolean;
};

export function getReadiness(item: CreativeItem | null): ReadinessEntry[] {
  const headline = item?.properties.headline ?? "";
  const cta = item?.properties.cta ?? "";
  const hasCreative =
    item !== null &&
    ["needs-review", "approved", "queued"].includes(item.status);

  return [
    {
      id: "headline",
      label: "Headline",
      done: headline.trim().length > 0 && headline.length <= HEADLINE_LIMIT,
    },
    {
      id: "description",
      label: "Description",
      done: hasCreative,
    },
    {
      id: "cta",
      label: "CTA",
      done: cta.trim().length > 0 && cta.length <= CTA_LIMIT,
    },
    {
      id: "creative",
      label: "Creative",
      done: hasCreative,
    },
    {
      id: "destination",
      label: "Destination",
      done: item?.status === "queued",
    },
  ];
}
