import { MOCK_PRODUCTS } from "@/features/products/mock-data";
import type { ContentDraft, ContentItem } from "./types";

function product(name: string) {
  const found = MOCK_PRODUCTS.find((item) => item.name === name);
  if (!found) throw new Error(`Unknown mock product: ${name}`);
  return found;
}

const reviewItems: {
  productName: string;
  priority: ContentItem["priority"];
  draft: ContentDraft;
}[] = [
  {
    productName: "Expandable Kitchen Storage Basket",
    priority: "high",
    draft: {
      title: "Expandable Kitchen Storage Basket | Countertop Organizer",
      description:
        "Two-tier expandable bamboo basket that slides to fit your cabinets, countertops, and shelves. Perfect for snacks, spices, and pantry staples — a natural way to keep your kitchen organized and clutter-free.",
      hashtags:
        "#KitchenOrganization #PantryIdeas #BambooStorage #HomeDecor #OrganizedHome",
      cta: "Save on Amazon",
      seoScore: 78,
    },
  },
  {
    productName: "Foldable Laundry Bag",
    priority: "high",
    draft: {
      title: "Foldable Laundry Bag | Collapsible Mesh Hamper",
      description:
        "Collapsible mesh laundry hamper with sturdy carry handles. Folds flat for easy storage between uses and makes hauling laundry to the machine a breeze.",
      hashtags: "#LaundryRoom #HomeOrganization #LaundryHack #StorageIdeas",
      cta: "Get it on Amazon",
      seoScore: 76,
    },
  },
  {
    productName: "Pantry Organizer Bins Set of 4",
    priority: "medium",
    draft: {
      title: "Pantry Organizer Bins (Set of 4) | Clear Storage",
      description:
        "Clear plastic storage bins with bamboo handles. Stackable for pantry and cabinet organization — see what's inside at a glance and keep shelves tidy.",
      hashtags: "#PantryOrganization #KitchenStorage #ClearBins #HomeOrganization",
      cta: "Shop on Amazon",
      seoScore: 74,
    },
  },
];

const doneItems: {
  productName: string;
  status: "approved" | "queued";
  priority: ContentItem["priority"];
  draft: ContentDraft;
}[] = [
  {
    productName: "Under-Sink Organizer",
    status: "approved",
    priority: "medium",
    draft: {
      title: "Under-Sink Organizer | Rolling Cabinet Storage",
      description:
        "Adjustable rolling organizer that fits around pipes. Two sliding drawers keep cleaning supplies easy to reach and out of the way.",
      hashtags:
        "#UnderSinkStorage #CleaningSupplies #KitchenOrganization #BathroomOrganization",
      cta: "Buy on Amazon",
      seoScore: 86,
    },
  },
  {
    productName: "Stackable Pantry Storage Jars",
    status: "queued",
    priority: "low",
    draft: {
      title: "Stackable Pantry Jars | Airtight Glass Canisters",
      description:
        "Airtight glass jars with wooden lids for flour, sugar, and pantry staples. Stackable, dishwasher-safe, and beautiful on any counter.",
      hashtags: "#PantryOrganization #GlassJars #KitchenStorage #ZeroWaste",
      cta: "Get it on Amazon",
      seoScore: 90,
    },
  },
];

const waitingItems: {
  productName: string;
  priority: ContentItem["priority"];
}[] = [
  { productName: "Closet Shelf Organizer", priority: "medium" },
  { productName: "Over-Door Shoe Rack", priority: "low" },
];

export const MOCK_CONTENT_ITEMS: ContentItem[] = [
  ...reviewItems.map((entry, index) => {
    const prod = product(entry.productName);
    return {
      id: `content_review_${index}`,
      productName: prod.name,
      category: prod.category,
      imageUrl: prod.imageUrl,
      priority: entry.priority,
      status: "needs-review" as const,
      hasChanges: false,
      draft: entry.draft,
    };
  }),
  ...waitingItems.map((entry, index) => {
    const prod = product(entry.productName);
    return {
      id: `content_waiting_${index}`,
      productName: prod.name,
      category: prod.category,
      imageUrl: prod.imageUrl,
      priority: entry.priority,
      status: "waiting" as const,
      hasChanges: false,
      draft: null,
    };
  }),
  {
    id: "content_generating_0",
    productName: "Bamboo Bathroom Shelf",
    category: product("Bamboo Bathroom Shelf").category,
    imageUrl: product("Bamboo Bathroom Shelf").imageUrl,
    priority: "high" as const,
    status: "generating" as const,
    hasChanges: false,
    draft: null,
  },
  ...doneItems.map((entry, index) => {
    const prod = product(entry.productName);
    return {
      id: `content_done_${index}`,
      productName: prod.name,
      category: prod.category,
      imageUrl: prod.imageUrl,
      priority: entry.priority,
      status: entry.status,
      hasChanges: false,
      draft: entry.draft,
    };
  }),
];
