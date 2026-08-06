import { MOCK_PRODUCTS } from "@/features/products/mock-data";
import { buildCreativeItem } from "./creative-utils";
import type {
  CreativeItem,
  CreativeTemplate,
  CreativeVariant,
  OverlayStyle,
  TemplateId,
  VariantId,
} from "./types";

export const CREATIVE_TEMPLATES: CreativeTemplate[] = [
  {
    id: "minimal",
    name: "Minimal",
    description: "Clean, airy, and focused on the product.",
    background: "#FAFAF8",
    accent: "#111111",
    text: "#111111",
  },
  {
    id: "modern",
    name: "Modern",
    description: "Dark scrim with crisp, centered typography.",
    background: "#1B1B1F",
    accent: "#FFFFFF",
    text: "#FFFFFF",
  },
  {
    id: "luxury",
    name: "Luxury",
    description: "Rich contrast with a refined gold accent.",
    background: "#18141B",
    accent: "#C9A227",
    text: "#F5EFE6",
  },
  {
    id: "lifestyle",
    name: "Lifestyle",
    description: "Bright, natural, and approachable.",
    background: "#FDF6EC",
    accent: "#2F6F5F",
    text: "#22302B",
  },
  {
    id: "bold",
    name: "Bold",
    description: "High-impact color and statement type.",
    background: "#1F2A44",
    accent: "#FF6B35",
    text: "#FFFFFF",
  },
];

export const CREATIVE_VARIANTS: CreativeVariant[] = [
  { id: "a", label: "Variant A", style: "Minimal", templateId: "minimal" },
  { id: "b", label: "Variant B", style: "Luxury", templateId: "luxury" },
  { id: "c", label: "Variant C", style: "Lifestyle", templateId: "lifestyle" },
  { id: "d", label: "Variant D", style: "Bold", templateId: "bold" },
];

export const LOGO_POSITION_OPTIONS: {
  value: CreativeItem["properties"]["logoPosition"];
  label: string;
}[] = [
  { value: "top-left", label: "Top left" },
  { value: "top-right", label: "Top right" },
  { value: "bottom-left", label: "Bottom left" },
  { value: "bottom-right", label: "Bottom right" },
];

export const OVERLAY_STYLE_OPTIONS: {
  value: OverlayStyle;
  label: string;
}[] = [
  { value: "none", label: "None" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "gradient", label: "Gradient" },
];

export const BRAND_OPTIONS = [
  "Atlas",
  "Atlas Affiliate",
  "Bright Living",
  "Home Hacks",
];

export const TEMPLATE_BY_ID = Object.fromEntries(
  CREATIVE_TEMPLATES.map((template) => [template.id, template]),
) as Record<TemplateId, CreativeTemplate>;

export const VARIANT_BY_ID = Object.fromEntries(
  CREATIVE_VARIANTS.map((variant) => [variant.id, variant]),
) as Record<VariantId, CreativeVariant>;

function product(name: string) {
  const found = MOCK_PRODUCTS.find((item) => item.name === name);
  if (!found) throw new Error(`Unknown mock product: ${name}`);
  return found;
}

const REVIEW_PLANS: {
  productName: string;
  priority: CreativeItem["priority"];
  templateId: TemplateId;
  selectedVariant: VariantId;
  overlayStyle: OverlayStyle;
}[] = [
  {
    productName: "Expandable Kitchen Storage Basket",
    priority: "high",
    templateId: "minimal",
    selectedVariant: "a",
    overlayStyle: "dark",
  },
  {
    productName: "Foldable Laundry Bag",
    priority: "high",
    templateId: "bold",
    selectedVariant: "d",
    overlayStyle: "gradient",
  },
  {
    productName: "Pantry Organizer Bins Set of 4",
    priority: "medium",
    templateId: "luxury",
    selectedVariant: "b",
    overlayStyle: "dark",
  },
];

const DONE_PLANS: {
  productName: string;
  status: "approved" | "queued";
  priority: CreativeItem["priority"];
  templateId: TemplateId;
  selectedVariant: VariantId;
  overlayStyle: OverlayStyle;
}[] = [
  {
    productName: "Under-Sink Organizer",
    status: "approved",
    priority: "medium",
    templateId: "lifestyle",
    selectedVariant: "c",
    overlayStyle: "light",
  },
  {
    productName: "Stackable Pantry Storage Jars",
    status: "queued",
    priority: "low",
    templateId: "minimal",
    selectedVariant: "a",
    overlayStyle: "dark",
  },
];

const WAITING_PLANS: {
  productName: string;
  priority: CreativeItem["priority"];
}[] = [
  { productName: "Closet Shelf Organizer", priority: "medium" },
  { productName: "Over-Door Shoe Rack", priority: "low" },
];

export const MOCK_CREATIVE_ITEMS: CreativeItem[] = [
  ...REVIEW_PLANS.map((plan, index) =>
    buildCreativeItem(product(plan.productName), {
      id: `creative_review_${index}`,
      priority: plan.priority,
      status: "needs-review",
      templateId: plan.templateId,
      selectedVariant: plan.selectedVariant,
      overlayStyle: plan.overlayStyle,
    }),
  ),
  ...WAITING_PLANS.map((plan, index) =>
    buildCreativeItem(product(plan.productName), {
      id: `creative_waiting_${index}`,
      priority: plan.priority,
      status: "waiting",
    }),
  ),
  buildCreativeItem(product("Bamboo Bathroom Shelf"), {
    id: "creative_generating_0",
    priority: "high",
    status: "generating",
  }),
  ...DONE_PLANS.map((plan, index) =>
    buildCreativeItem(product(plan.productName), {
      id: `creative_done_${index}`,
      priority: plan.priority,
      status: plan.status,
      templateId: plan.templateId,
      selectedVariant: plan.selectedVariant,
      overlayStyle: plan.overlayStyle,
    }),
  ),
];
