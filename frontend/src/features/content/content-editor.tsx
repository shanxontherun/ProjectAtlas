"use client";

import {
  Copy,
  Eye,
  Hourglass,
  Maximize2,
  Minimize2,
  RefreshCw,
  RotateCcw,
  WandSparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ProgressBar } from "@/features/products/progress-bar";
import { ProductImage } from "@/features/products/product-image";
import { ContentStatusBadge } from "./content-status-badge";
import { DESCRIPTION_LIMIT, TITLE_LIMIT, type ContentDraft, type ContentItem, type EditorAction } from "./types";

function isSameDraft(a: ContentDraft, b: ContentDraft) {
  return (
    a.title === b.title &&
    a.description === b.description &&
    a.hashtags === b.hashtags &&
    a.cta === b.cta &&
    a.seoScore === b.seoScore
  );
}

function seoTone(score: number) {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 60) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

type ContentEditorProps = {
  item: ContentItem | null;
  draft: ContentDraft | null;
  readOnly: boolean;
  feedback: string | null;
  onDraftChange: (draft: ContentDraft) => void;
  onAction: (action: EditorAction) => void;
  onPreview: () => void;
};

export function ContentEditor({
  item,
  draft,
  readOnly,
  feedback,
  onDraftChange,
  onAction,
  onPreview,
}: ContentEditorProps) {
  if (!item) {
    return (
      <section className="flex min-h-[28rem] items-center justify-center rounded-xl border border-dashed bg-card/50 px-6 py-16 text-center">
        <div className="space-y-2">
          <p className="text-sm font-semibold tracking-tight">
            Select a product from the queue
          </p>
          <p className="mx-auto max-w-sm text-sm leading-relaxed text-muted-foreground">
            Its Pinterest content will open here for review, editing, and approval.
          </p>
        </div>
      </section>
    );
  }

  if (!item.draft) {
    if (item.status === "generating") {
      return (
        <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-3">
            <span className="relative size-12 shrink-0 overflow-hidden rounded-lg border bg-muted">
              <ProductImage src={item.imageUrl} alt={item.productName} />
            </span>
            <div className="min-w-0">
              <h2 className="truncate text-sm font-semibold tracking-tight">
                {item.productName}
              </h2>
              <p className="text-xs text-muted-foreground">
                Generating Pinterest content…
              </p>
            </div>
          </div>
          <div aria-hidden="true" className="flex flex-col gap-3">
            <div className="h-8 animate-pulse rounded-lg bg-muted" />
            <div className="h-24 animate-pulse rounded-lg bg-muted" />
            <div className="h-8 animate-pulse rounded-lg bg-muted" />
            <div className="h-8 w-2/3 animate-pulse rounded-lg bg-muted" />
          </div>
        </section>
      );
    }

    return (
      <section className="flex min-h-[28rem] flex-col items-center justify-center rounded-xl border border-dashed bg-card/50 px-6 py-16 text-center">
        <span className="flex size-12 items-center justify-center rounded-xl border bg-muted/50 text-muted-foreground">
          <Hourglass className="size-6" aria-hidden="true" />
        </span>
        <h2 className="mt-4 text-base font-semibold tracking-tight">
          Waiting for generation
        </h2>
        <p className="mt-1 max-w-sm text-sm leading-relaxed text-muted-foreground">
          This product is queued for AI content. Use{" "}
          <span className="font-medium text-foreground">Generate AI Content</span>{" "}
          to create its Pinterest title, description, and hashtags.
        </p>
      </section>
    );
  }

  const dirty = !isSameDraft(draft ?? item.draft, item.draft);
  const working = draft ?? item.draft;
  const titleCount = working.title.length;
  const descriptionCount = working.description.length;

  const fieldId = (suffix: string) => `${item.id}-${suffix}`;

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="relative size-12 shrink-0 overflow-hidden rounded-lg border bg-muted">
            <ProductImage src={item.imageUrl} alt={item.productName} />
          </span>
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold tracking-tight">
              {item.productName}
            </h2>
            <p className="mt-0.5 text-xs text-muted-foreground">{item.category}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            aria-label={`Preview ${item.productName}`}
            onClick={onPreview}
          >
            <Eye data-icon="inline-start" className="size-3.5" />
            Preview
          </Button>
          <ContentStatusBadge status={item.status} />
        </div>
      </header>

      {item.hasChanges && item.status === "needs-review" && (
        <div className="rounded-lg border border-amber-500/25 bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-400">
          Changes requested — edit the draft, then approve or queue it.
        </div>
      )}

      <div className="grid gap-5">
        <div className="space-y-1.5">
          <div className="flex items-baseline justify-between gap-2">
            <label
              htmlFor={fieldId("title")}
              className="text-xs font-medium text-muted-foreground"
            >
              Pinterest Title
            </label>
            <span
              className={cn(
                "text-xs tabular-nums",
                titleCount > TITLE_LIMIT
                  ? "font-medium text-red-600 dark:text-red-400"
                  : "text-muted-foreground",
              )}
            >
              {titleCount} / {TITLE_LIMIT}
            </span>
          </div>
          <Input
            id={fieldId("title")}
            value={working.title}
            disabled={readOnly}
            aria-label="Pinterest title"
            onChange={(event) =>
              onDraftChange({ ...working, title: event.target.value })
            }
          />
        </div>

        <div className="space-y-1.5">
          <div className="flex items-baseline justify-between gap-2">
            <label
              htmlFor={fieldId("description")}
              className="text-xs font-medium text-muted-foreground"
            >
              Pinterest Description
            </label>
            <span
              className={cn(
                "text-xs tabular-nums",
                descriptionCount > DESCRIPTION_LIMIT
                  ? "font-medium text-red-600 dark:text-red-400"
                  : "text-muted-foreground",
              )}
            >
              {descriptionCount} / {DESCRIPTION_LIMIT}
            </span>
          </div>
          <Textarea
            id={fieldId("description")}
            rows={6}
            value={working.description}
            disabled={readOnly}
            aria-label="Pinterest description"
            onChange={(event) =>
              onDraftChange({ ...working, description: event.target.value })
            }
          />
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label
              htmlFor={fieldId("hashtags")}
              className="text-xs font-medium text-muted-foreground"
            >
              Hashtags
            </label>
            <Input
              id={fieldId("hashtags")}
              value={working.hashtags}
              disabled={readOnly}
              aria-label="Hashtags"
              onChange={(event) =>
                onDraftChange({ ...working, hashtags: event.target.value })
              }
            />
          </div>
          <div className="space-y-1.5">
            <label
              htmlFor={fieldId("cta")}
              className="text-xs font-medium text-muted-foreground"
            >
              Call to Action
            </label>
            <Input
              id={fieldId("cta")}
              value={working.cta}
              disabled={readOnly}
              aria-label="Call to action"
              onChange={(event) =>
                onDraftChange({ ...working, cta: event.target.value })
              }
            />
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-muted/40 p-3.5">
        <div className="mb-2 flex items-center justify-between gap-2">
          <span className="text-xs font-medium">SEO Score</span>
          <span className={cn("text-xs font-medium tabular-nums", seoTone(working.seoScore))}>
            {working.seoScore} / 100
          </span>
        </div>
        <ProgressBar value={working.seoScore} showValue={false} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" size="sm" variant="outline" onClick={() => onAction("copy")}>
          <Copy data-icon="inline-start" className="size-3.5" />
          Copy
        </Button>
        <Button type="button" size="sm" variant="outline" disabled={readOnly} onClick={() => onAction("improve")}>
          <WandSparkles data-icon="inline-start" className="size-3.5" />
          Improve
        </Button>
        <Button type="button" size="sm" variant="outline" disabled={readOnly} onClick={() => onAction("regenerate")}>
          <RefreshCw data-icon="inline-start" className="size-3.5" />
          Regenerate
        </Button>
        <Button type="button" size="sm" variant="outline" disabled={readOnly} onClick={() => onAction("shorten")}>
          <Minimize2 data-icon="inline-start" className="size-3.5" />
          Shorten
        </Button>
        <Button type="button" size="sm" variant="outline" disabled={readOnly} onClick={() => onAction("expand")}>
          <Maximize2 data-icon="inline-start" className="size-3.5" />
          Expand
        </Button>
        <div className="min-w-4 flex-1" />
        <Button type="button" size="sm" variant="ghost" disabled={readOnly || !dirty} onClick={() => onAction("reset")}>
          <RotateCcw data-icon="inline-start" className="size-3.5" />
          Reset
        </Button>
      </div>

      {feedback && (
        <p className="-mt-2 text-xs text-muted-foreground">{feedback}</p>
      )}
    </section>
  );
}
