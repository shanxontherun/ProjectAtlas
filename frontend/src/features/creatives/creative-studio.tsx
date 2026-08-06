"use client";

import { useEffect, useRef, useState } from "react";
import { Layers, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MOCK_CREATIVE_ITEMS } from "./mock-data";
import {
  getCreativeCounts,
  nextVariant,
  sortCreativeItems,
  VARIANT_TEMPLATE_MAP,
  variantForTemplate,
} from "./creative-utils";
import { ApprovalPanel } from "./approval-panel";
import { AtlasRecommendation } from "./atlas-recommendation";
import { CreativeEmptyState } from "./creative-empty-state";
import { CreativePreview } from "./creative-preview";
import { CreativeQueue } from "./creative-queue";
import { CreativeScore } from "./creative-score";
import { CreativeSkeleton } from "./creative-skeleton";
import { CreativeSummary } from "./creative-summary";
import { PropertiesPanel } from "./properties-panel";
import { ReadinessChecklist } from "./readiness-checklist";
import { TemplateGallery } from "./template-gallery";
import { VariantGallery } from "./variant-gallery";
import type {
  CreativeItem,
  CreativeProperties,
  TemplateId,
  VariantId,
} from "./types";

const GENERATION_DELAY = 1600;

export function CreativeStudio() {
  const [items, setItems] = useState<CreativeItem[]>(MOCK_CREATIVE_ITEMS);
  const [selectedId, setSelectedId] = useState<string | null>(() => {
    const firstReview = MOCK_CREATIVE_ITEMS.find(
      (item) => item.status === "needs-review",
    );
    return firstReview?.id ?? null;
  });
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<string | null>(null);

  const selectedIdRef = useRef<string | null>(null);
  const feedbackTimer = useRef<number | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setLoading(false), 650);
    return () => window.clearTimeout(timer);
  }, []);

  const counts = getCreativeCounts(items);
  const waitingCount = counts.waiting;
  const selectedItem = items.find((item) => item.id === selectedId) ?? null;

  function selectItem(item: CreativeItem) {
    setSelectedId(item.id);
    selectedIdRef.current = item.id;
    setFeedback(null);
  }

  function patchItem(id: string, patch: Partial<CreativeItem>) {
    setItems((current) =>
      current.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    );
  }

  function showFeedback(message: string) {
    setFeedback(message);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setFeedback(null), 2200);
  }

  function generateWaiting(limit: number) {
    const targets = items
      .filter((item) => item.status === "waiting")
      .slice(0, limit);
    if (targets.length === 0) return;

    setItems((current) =>
      current.map((item) =>
        targets.some((target) => target.id === item.id)
          ? { ...item, status: "generating" }
          : item,
      ),
    );

    const first = targets[0];
    setSelectedId(first.id);
    selectedIdRef.current = first.id;
    setFeedback(null);

    targets.forEach((target) => {
      window.setTimeout(() => {
        setItems((current) =>
          current.map((item) =>
            item.id === target.id && item.status === "generating"
              ? { ...item, status: "needs-review" }
              : item,
          ),
        );
      }, GENERATION_DELAY);
    });
  }

  function approve() {
    if (!selectedItem) return;
    patchItem(selectedItem.id, { status: "approved" });
    showFeedback("Approved — ready to queue for publishing.");
  }

  function queueForPublishing() {
    if (!selectedItem) return;
    patchItem(selectedItem.id, { status: "queued" });
    showFeedback("Queued for publishing.");
  }

  function regenerate() {
    if (!selectedItem) return;
    const next = nextVariant(selectedItem.selectedVariant);
    patchItem(selectedItem.id, {
      selectedVariant: next,
      templateId: VARIANT_TEMPLATE_MAP[next],
    });
    showFeedback("Regenerated — created a new variant of this creative.");
  }

  function generateVariants() {
    if (!selectedItem) return;
    patchItem(selectedItem.id, { selectedVariant: "a", templateId: "minimal" });
    showFeedback("Generated four new variants to compare.");
  }

  function selectVariant(variantId: VariantId) {
    if (!selectedItem) return;
    patchItem(selectedItem.id, {
      selectedVariant: variantId,
      templateId: VARIANT_TEMPLATE_MAP[variantId],
    });
  }

  function selectTemplate(templateId: TemplateId) {
    if (!selectedItem) return;
    const variant = variantForTemplate(templateId);
    patchItem(selectedItem.id, {
      templateId,
      ...(variant ? { selectedVariant: variant } : {}),
    });
  }

  function updateProperties(patch: Partial<CreativeProperties>) {
    if (!selectedItem) return;
    patchItem(selectedItem.id, {
      properties: { ...selectedItem.properties, ...patch },
    });
  }

  if (loading) {
    return <CreativeSkeleton />;
  }

  const sorted = sortCreativeItems(items);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            Creative Studio
          </h1>
          <p className="text-sm text-muted-foreground">
            Review and approve Pinterest creatives generated by Atlas.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            onClick={() => generateWaiting(1)}
            disabled={waitingCount === 0}
          >
            <Sparkles data-icon="inline-start" className="size-4" />
            Generate Creatives
          </Button>
          <Button
            variant="outline"
            onClick={() => generateWaiting(waitingCount)}
            disabled={waitingCount === 0}
          >
            <Layers data-icon="inline-start" className="size-4" />
            Batch Generate
          </Button>
        </div>
      </header>

      <CreativeSummary items={items} />

      {items.length === 0 ? (
        <CreativeEmptyState
          onGenerate={() => generateWaiting(waitingCount)}
          canGenerate={false}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(250px,1fr)_3fr]">
            <div className="order-1 flex flex-col gap-6 lg:order-none lg:col-start-2 lg:row-start-1">
              <CreativePreview item={selectedItem} />
              <VariantGallery item={selectedItem} onSelect={selectVariant} />
            </div>
            <div className="order-2 lg:order-none lg:col-start-1 lg:row-start-1">
              <CreativeQueue
                items={sorted}
                selectedId={selectedId}
                onSelect={selectItem}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <CreativeScore />
            <AtlasRecommendation item={selectedItem} />
            <ReadinessChecklist item={selectedItem} />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
            <TemplateGallery item={selectedItem} onSelect={selectTemplate} />
            <PropertiesPanel item={selectedItem} onChange={updateProperties} />
          </div>

          <ApprovalPanel
            item={selectedItem}
            feedback={feedback}
            onApprove={approve}
            onRegenerate={regenerate}
            onGenerateVariants={generateVariants}
            onQueue={queueForPublishing}
          />
        </>
      )}
    </div>
  );
}
