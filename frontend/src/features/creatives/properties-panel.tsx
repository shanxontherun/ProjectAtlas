"use client";

import { SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  BRAND_OPTIONS,
  LOGO_POSITION_OPTIONS,
  OVERLAY_STYLE_OPTIONS,
} from "./mock-data";
import {
  CTA_LIMIT,
  HEADLINE_LIMIT,
  type CreativeItem,
  type CreativeProperties,
} from "./types";

type PropertiesPanelProps = {
  item: CreativeItem | null;
  onChange: (patch: Partial<CreativeProperties>) => void;
};

export function PropertiesPanel({ item, onChange }: PropertiesPanelProps) {
  if (!item) {
    return (
      <section className="flex min-h-[22rem] flex-col items-center justify-center rounded-xl border border-dashed bg-card/50 px-6 py-16 text-center">
        <span className="flex size-12 items-center justify-center rounded-xl border bg-muted/50 text-muted-foreground">
          <SlidersHorizontal className="size-6" aria-hidden="true" />
        </span>
        <h2 className="mt-4 text-base font-semibold tracking-tight">
          No creative selected
        </h2>
        <p className="mt-1 max-w-sm text-sm leading-relaxed text-muted-foreground">
          Select a creative from the queue to edit its headline, call to
          action, and branding.
        </p>
      </section>
    );
  }

  const readOnly = item.status === "queued";
  const properties = item.properties;
  const fieldId = (suffix: string) => `${item.id}-${suffix}`;

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="space-y-0.5">
        <h2 className="text-sm font-semibold tracking-tight">Properties</h2>
        <p className="text-xs text-muted-foreground">
          Lightweight edits — no graphic editor needed.
        </p>
      </header>

      {readOnly && (
        <div className="rounded-lg border border-chart-2/25 bg-chart-2/10 px-3 py-2 text-xs text-chart-2">
          This creative is queued for publishing and locked for editing.
        </div>
      )}

      <div className="flex flex-col gap-4">
        <div className="space-y-1.5">
          <div className="flex items-baseline justify-between gap-2">
            <label
              htmlFor={fieldId("headline")}
              className="text-xs font-medium text-muted-foreground"
            >
              Headline
            </label>
            <span
              className={cn(
                "text-xs tabular-nums",
                properties.headline.length > HEADLINE_LIMIT
                  ? "font-medium text-red-600 dark:text-red-400"
                  : "text-muted-foreground",
              )}
            >
              {properties.headline.length} / {HEADLINE_LIMIT}
            </span>
          </div>
          <Input
            id={fieldId("headline")}
            value={properties.headline}
            disabled={readOnly}
            aria-label="Headline"
            onChange={(event) => onChange({ headline: event.target.value })}
          />
        </div>

        <div className="space-y-1.5">
          <div className="flex items-baseline justify-between gap-2">
            <label
              htmlFor={fieldId("cta")}
              className="text-xs font-medium text-muted-foreground"
            >
              Call to Action
            </label>
            <span
              className={cn(
                "text-xs tabular-nums",
                properties.cta.length > CTA_LIMIT
                  ? "font-medium text-red-600 dark:text-red-400"
                  : "text-muted-foreground",
              )}
            >
              {properties.cta.length} / {CTA_LIMIT}
            </span>
          </div>
          <Input
            id={fieldId("cta")}
            value={properties.cta}
            disabled={readOnly}
            aria-label="Call to action"
            onChange={(event) => onChange({ cta: event.target.value })}
          />
        </div>

        <div className="space-y-1.5">
          <label
            htmlFor={fieldId("brand")}
            className="text-xs font-medium text-muted-foreground"
          >
            Brand
          </label>
          <Select
            value={properties.brand}
            disabled={readOnly}
            onValueChange={(value) => onChange({ brand: value })}
          >
            <SelectTrigger
              id={fieldId("brand")}
              aria-label="Brand"
              className="w-full"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent align="start">
              {BRAND_OPTIONS.map((brand) => (
                <SelectItem key={brand} value={brand}>
                  {brand}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label
              htmlFor={fieldId("logo")}
              className="text-xs font-medium text-muted-foreground"
            >
              Logo Position
            </label>
            <Select
              value={properties.logoPosition}
              disabled={readOnly}
              onValueChange={(value) =>
                onChange({
                  logoPosition: value as CreativeProperties["logoPosition"],
                })
              }
            >
              <SelectTrigger
                id={fieldId("logo")}
                aria-label="Logo position"
                className="w-full"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent align="start">
                {LOGO_POSITION_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor={fieldId("overlay")}
              className="text-xs font-medium text-muted-foreground"
            >
              Overlay Style
            </label>
            <Select
              value={properties.overlayStyle}
              disabled={readOnly}
              onValueChange={(value) =>
                onChange({
                  overlayStyle: value as CreativeProperties["overlayStyle"],
                })
              }
            >
              <SelectTrigger
                id={fieldId("overlay")}
                aria-label="Overlay style"
                className="w-full"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent align="start">
                {OVERLAY_STYLE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </section>
  );
}
