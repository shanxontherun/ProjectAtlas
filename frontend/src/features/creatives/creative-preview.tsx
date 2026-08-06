"use client";

import { ImageIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ContentStatusBadge } from "@/features/content/content-status-badge";
import { ProductImage } from "@/features/products/product-image";
import { TEMPLATE_BY_ID, VARIANT_BY_ID } from "./mock-data";
import type {
  CreativeItem,
  CreativePriority,
  CreativeProperties,
  CreativeTemplate,
  LogoPosition,
  OverlayStyle,
  TemplateId,
} from "./types";

const OVERLAY_CLASSES: Record<OverlayStyle, string | null> = {
  none: null,
  light: "bg-white/20",
  dark: "bg-black/45",
  gradient: "bg-gradient-to-t from-black/70 via-black/25 to-black/5",
};

const LOGO_POSITIONS: Record<LogoPosition, string> = {
  "top-left": "left-3 top-3",
  "top-right": "right-3 top-3",
  "bottom-left": "bottom-3 left-3",
  "bottom-right": "bottom-3 right-3",
};

const PRIORITY_META: Record<CreativePriority, { label: string; dotClass: string }> = {
  high: { label: "High priority", dotClass: "bg-red-500" },
  medium: { label: "Medium priority", dotClass: "bg-amber-500" },
  low: { label: "Low priority", dotClass: "bg-emerald-500" },
};

type PinStyle = {
  eyebrow: (category: string) => string | null;
  eyebrowClass: string;
  headlineClass: string;
  ctaClass: string;
  scrimClass: string;
  layoutClass: string;
  align: "start" | "center";
  divider?: boolean;
};

const PIN_STYLES: Record<TemplateId, PinStyle> = {
  minimal: {
    eyebrow: (category) => category.toUpperCase(),
    eyebrowClass:
      "text-[10px] font-semibold uppercase tracking-[0.2em] text-white/75",
    headlineClass:
      "mt-1.5 max-w-[16ch] text-xl leading-tight font-semibold tracking-tight text-white",
    ctaClass: "bg-white text-black",
    scrimClass: "bg-gradient-to-t from-black/50 via-black/20 to-transparent",
    layoutClass: "items-start justify-end",
    align: "start",
  },
  modern: {
    eyebrow: () => "MODERN",
    eyebrowClass:
      "text-[10px] font-semibold uppercase tracking-[0.35em] text-white/60",
    headlineClass:
      "mt-2 max-w-[15ch] text-2xl leading-tight font-bold tracking-tight text-white",
    ctaClass: "border border-white/70 bg-white/10 text-white backdrop-blur-sm",
    scrimClass: "bg-gradient-to-t from-black/60 via-black/25 to-black/10",
    layoutClass: "items-center justify-center text-center",
    align: "center",
  },
  luxury: {
    eyebrow: () => "LUXURY PICK",
    eyebrowClass:
      "text-[10px] font-semibold uppercase tracking-[0.3em] text-[#E4C87A]",
    headlineClass:
      "mt-1.5 max-w-[16ch] text-2xl leading-tight font-semibold tracking-tight text-[#F7F1E6]",
    ctaClass: "bg-[#C9A227] text-[#1A1410]",
    scrimClass: "bg-gradient-to-t from-black/55 via-black/25 to-transparent",
    layoutClass: "items-start justify-end",
    align: "start",
    divider: true,
  },
  lifestyle: {
    eyebrow: () => "WEEKEND PROJECT",
    eyebrowClass:
      "text-[10px] font-semibold uppercase tracking-[0.25em] text-[#2F6F5F]",
    headlineClass:
      "mt-1.5 max-w-[16ch] text-xl leading-tight font-semibold tracking-tight text-[#22302B]",
    ctaClass: "bg-[#2F6F5F] text-white",
    scrimClass: "bg-gradient-to-t from-white/40 via-transparent to-transparent",
    layoutClass: "items-start justify-end",
    align: "start",
  },
  bold: {
    eyebrow: () => null,
    eyebrowClass: "",
    headlineClass:
      "mt-0 max-w-[12ch] text-[1.7rem] leading-[0.95] font-extrabold uppercase tracking-tight text-white",
    ctaClass: "bg-[#FF6B35] text-white",
    scrimClass: "bg-gradient-to-t from-black/60 via-black/30 to-black/10",
    layoutClass: "items-center justify-center text-center",
    align: "center",
  },
};

export type CreativePinProps = {
  imageUrl: string;
  productName: string;
  category: string;
  template: CreativeTemplate;
  properties: CreativeProperties;
  className?: string;
};

export function CreativePin({
  imageUrl,
  productName,
  category,
  template,
  properties,
  className,
}: CreativePinProps) {
  const style = PIN_STYLES[template.id];
  const overlay = OVERLAY_CLASSES[properties.overlayStyle];
  const eyebrow = style.eyebrow(category);

  return (
    <div
      className={cn(
        "relative aspect-[2/3] w-full overflow-hidden rounded-xl bg-muted",
        className,
      )}
    >
      <ProductImage src={imageUrl} alt={productName} />
      <div className={cn("absolute inset-0", style.scrimClass)} aria-hidden="true" />
      {overlay && (
        <div className={cn("absolute inset-0", overlay)} aria-hidden="true" />
      )}

      <span
        className={cn(
          "absolute rounded-full bg-black/45 px-2 py-0.5 text-[9px] font-semibold tracking-wide text-white backdrop-blur-sm",
          LOGO_POSITIONS[properties.logoPosition],
        )}
      >
        {properties.brand}
      </span>

      <div
        className={cn(
          "absolute inset-0 flex flex-col p-4",
          style.layoutClass,
        )}
      >
        {eyebrow && <span className={style.eyebrowClass}>{eyebrow}</span>}
        {style.divider && (
          <span
            className="mt-3 h-px w-10 bg-[#C9A227]"
            aria-hidden="true"
          />
        )}
        <h3 className={style.headlineClass}>{properties.headline}</h3>
        <span
          className={cn(
            "mt-3 inline-flex w-fit rounded-full px-3 py-1.5 text-[10px] font-semibold tracking-wide",
            style.ctaClass,
            style.align === "center" ? "mx-auto" : "self-start",
          )}
        >
          {properties.cta}
        </span>
      </div>
    </div>
  );
}

type CreativePreviewProps = {
  item: CreativeItem | null;
};

export function CreativePreview({ item }: CreativePreviewProps) {
  if (!item) {
    return (
      <section className="flex min-h-[30rem] flex-col items-center justify-center rounded-xl border border-dashed bg-card/50 px-6 py-16 text-center">
        <span className="flex size-12 items-center justify-center rounded-xl border bg-muted/50 text-muted-foreground">
          <ImageIcon className="size-6" aria-hidden="true" />
        </span>
        <h2 className="mt-4 text-base font-semibold tracking-tight">
          Select a creative to review
        </h2>
        <p className="mt-1 max-w-sm text-sm leading-relaxed text-muted-foreground">
          Its generated Pinterest pin will open here for comparison, editing, and
          approval.
        </p>
      </section>
    );
  }

  const template = TEMPLATE_BY_ID[item.templateId];
  const variant = VARIANT_BY_ID[item.selectedVariant];
  const priority = PRIORITY_META[item.priority];

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="relative size-11 shrink-0 overflow-hidden rounded-lg border bg-muted">
            <ProductImage src={item.imageUrl} alt={item.productName} />
          </span>
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold tracking-tight">
              {item.productName}
            </h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {item.category}
            </p>
          </div>
        </div>
        <ContentStatusBadge status={item.status} />
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">{template.name} template</Badge>
        <Badge variant="outline">
          {variant.label} · {variant.style}
        </Badge>
        <Badge variant="outline">{item.properties.brand}</Badge>
        <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
          <span
            className={cn("size-1.5 rounded-full", priority.dotClass)}
            aria-hidden="true"
          />
          {priority.label}
        </span>
      </div>

      <div className="flex justify-center rounded-xl bg-muted/40 px-6 py-7">
        <div className="w-full max-w-[23rem]">
          <CreativePin
            imageUrl={item.imageUrl}
            productName={item.productName}
            category={item.category}
            template={template}
            properties={item.properties}
            className="shadow-xl shadow-black/10"
          />
        </div>
      </div>
    </section>
  );
}
