export type CreativeStatus =
  | "waiting"
  | "generating"
  | "needs-review"
  | "approved"
  | "queued";

export type CreativePriority = "high" | "medium" | "low";

export type TemplateId =
  | "minimal"
  | "modern"
  | "luxury"
  | "lifestyle"
  | "bold";

export type VariantId = "a" | "b" | "c" | "d";

export type LogoPosition =
  | "top-left"
  | "top-right"
  | "bottom-left"
  | "bottom-right";

export type OverlayStyle = "none" | "light" | "dark" | "gradient";

export type CreativeProperties = {
  headline: string;
  cta: string;
  brand: string;
  logoPosition: LogoPosition;
  overlayStyle: OverlayStyle;
};

export type CreativeTemplate = {
  id: TemplateId;
  name: string;
  description: string;
  background: string;
  accent: string;
  text: string;
};

export type CreativeVariant = {
  id: VariantId;
  label: string;
  style: string;
  templateId: TemplateId;
};

export type CreativeItem = {
  id: string;
  productName: string;
  category: string;
  imageUrl: string;
  priority: CreativePriority;
  status: CreativeStatus;
  selectedVariant: VariantId;
  templateId: TemplateId;
  properties: CreativeProperties;
};

export const HEADLINE_LIMIT = 90;
export const CTA_LIMIT = 40;
