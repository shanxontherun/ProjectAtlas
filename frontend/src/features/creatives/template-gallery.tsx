"use client";

import { cn } from "@/lib/utils";
import { CREATIVE_TEMPLATES } from "./mock-data";
import type { CreativeItem, TemplateId } from "./types";

type TemplateGalleryProps = {
  item: CreativeItem | null;
  onSelect: (templateId: TemplateId) => void;
};

export function TemplateGallery({ item, onSelect }: TemplateGalleryProps) {
  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="flex items-center justify-between gap-2">
        <div className="space-y-0.5">
          <h2 className="text-sm font-semibold tracking-tight">Templates</h2>
          <p className="text-xs text-muted-foreground">
            Switch the visual style of this creative.
          </p>
        </div>
        <span className="text-xs tabular-nums text-muted-foreground">
          {CREATIVE_TEMPLATES.length} templates
        </span>
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {CREATIVE_TEMPLATES.map((template) => {
          const active = item?.templateId === template.id;

          return (
            <button
              key={template.id}
              type="button"
              disabled={!item}
              onClick={() => onSelect(template.id)}
              aria-pressed={active}
              className={cn(
                "group flex flex-col gap-2 rounded-lg border p-2 text-left outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50",
                active
                  ? "border-primary bg-muted/50"
                  : "border-border hover:bg-muted/40",
              )}
            >
              <div
                className="relative aspect-[4/3] w-full overflow-hidden rounded-md border"
                style={{ backgroundColor: template.background }}
              >
                <div className="absolute inset-0 flex flex-col justify-between p-2.5">
                  <span
                    className="text-[9px] font-semibold tracking-wide"
                    style={{ color: template.accent }}
                  >
                    Atlas
                  </span>
                  <span
                    className="text-sm leading-none font-bold"
                    style={{ color: template.text }}
                  >
                    Aa
                  </span>
                  <span
                    className="h-1 w-8 rounded-full"
                    style={{ backgroundColor: template.accent }}
                  />
                </div>
              </div>
              <span className="flex flex-col">
                <span
                  className={cn(
                    "text-xs font-medium",
                    active ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  {template.name}
                </span>
                <span className="line-clamp-2 text-[0.7rem] leading-snug text-muted-foreground">
                  {template.description}
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
