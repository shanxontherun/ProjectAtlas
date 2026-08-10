"use client";

import { useMemo, useRef, useState } from "react";
import { Layers, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  getCreativeCounts,
  nextVariant,
  sortCreativeItems,
  VARIANT_TEMPLATE_MAP,
  variantForTemplate,
} from "./creative-utils";
import { buildPresentationPayload } from "./creative-api";
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
import {
  useApproveCreative,
  useCreatives,
  useGenerateCreative,
  useReopenCreative,
  useSaveCreative,
} from "./use-creatives";
import { useQueueCreative, useRemoveCreative } from "@/features/publishing/use-publishing";
import type {
  CreativeItem,
  CreativeProperties,
  TemplateId,
  VariantId,
} from "./types";

type CreativePatch = {
  status?: CreativeItem["status"];
  templateId?: TemplateId;
  selectedVariant?: VariantId;
  properties?: CreativeProperties;
};

const SAVE_DEBOUNCE_MS = 600;

function isLocked(item: CreativeItem | null) {
  return (
    item !== null &&
    (item.status === "approved" || item.status === "queued")
  );
}

export function CreativeStudio() {
  const {
    data: serverItems = [],
    isLoading,
    isError,
    refetch,
  } = useCreatives();

  const generateMutation = useGenerateCreative();
  const approveMutation = useApproveCreative();
  const saveMutation = useSaveCreative();
  const reopenMutation = useReopenCreative();
  const queueMutation = useQueueCreative();
  const removeQueueMutation = useRemoveCreative();

  // Transient presentation states (generating / queued) and local
  // variant, template and property edits live in the browser until the
  // debounced save persists them; the backend always wins on fetch.
  const [transient, setTransient] = useState<Record<string, CreativePatch>>(
    {},
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [reopenTarget, setReopenTarget] = useState<CreativeItem | null>(null);

  const feedbackTimer = useRef<number | null>(null);
  const saveTimers = useRef<Record<string, number | null>>({});

  const items = useMemo(
    () =>
      serverItems.map((item) => {
        const patch = transient[item.id];
        if (!patch) return item;
        if (patch.status === "generating" && item.status !== "waiting") {
          return item;
        }
        return {
          ...item,
          status: patch.status ?? item.status,
          templateId: patch.templateId ?? item.templateId,
          selectedVariant: patch.selectedVariant ?? item.selectedVariant,
          properties: patch.properties ?? item.properties,
        };
      }),
    [serverItems, transient],
  );

  const counts = getCreativeCounts(items);
  const waitingCount = counts.waiting;
  // Fall back to the first item awaiting review until the user selects one.
  const autoSelectedId =
    items.find((item) => item.status === "needs-review")?.id ?? null;
  const activeSelectedId = selectedId ?? autoSelectedId;
  const selectedItem =
    items.find((item) => item.id === activeSelectedId) ?? null;

  function selectItem(item: CreativeItem) {
    setSelectedId(item.id);
    setFeedback(null);
  }

  function patchTransient(itemId: string, patch: CreativePatch) {
    setTransient((current) => ({
      ...current,
      [itemId]: { ...current[itemId], ...patch },
    }));
  }

  function clearTransient(itemId: string) {
    setTransient((current) => {
      const next = { ...current };
      delete next[itemId];
      return next;
    });
  }

  function showFeedback(message: string) {
    setFeedback(message);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setFeedback(null), 2200);
  }

  function persistPresentation(item: CreativeItem) {
    saveMutation.mutate(
      {
        researchProductId: Number(item.id),
        presentation: buildPresentationPayload(item),
      },
      {
        onError: () => showFeedback("Couldn't save your edits"),
      },
    );
  }

  function scheduleSave(item: CreativeItem) {
    const existing = saveTimers.current[item.id];
    if (existing !== null && existing !== undefined) {
      window.clearTimeout(existing);
    }
    saveTimers.current[item.id] = window.setTimeout(() => {
      saveTimers.current[item.id] = null;
      if (!isLocked(item)) {
        persistPresentation(item);
      }
    }, SAVE_DEBOUNCE_MS);
  }

  async function generateWaiting(limit: number) {
    const targets = items
      .filter((item) => item.status === "waiting")
      .slice(0, limit);
    if (targets.length === 0) return;

    const first = targets[0];
    setSelectedId(first.id);
    setFeedback(null);

    targets.forEach((target) => {
      patchTransient(target.id, { status: "generating" });
    });

    for (const target of targets) {
      try {
        await generateMutation.mutateAsync({
          researchProductId: Number(target.id),
        });
      } catch {
        clearTransient(target.id);
        showFeedback(`Couldn't generate a creative for ${target.productName}`);
      }
    }
  }

  async function approve() {
    if (!selectedItem || isLocked(selectedItem)) return;
    patchTransient(selectedItem.id, { status: "approved" });
    try {
      await approveMutation.mutateAsync({
        researchProductId: Number(selectedItem.id),
        presentation: buildPresentationPayload(selectedItem),
      });
      clearTransient(selectedItem.id);
      showFeedback("Approved — ready to queue for publishing.");
    } catch {
      clearTransient(selectedItem.id);
      showFeedback("Couldn't approve this creative");
    }
  }

  async function queueForPublishing() {
    if (!selectedItem || isLocked(selectedItem)) return;
    patchTransient(selectedItem.id, { status: "queued" });
    try {
      await queueMutation.mutateAsync(Number(selectedItem.id));
      clearTransient(selectedItem.id);
      showFeedback("Queued for publishing.");
    } catch {
      clearTransient(selectedItem.id);
      showFeedback("Couldn't queue this creative");
    }
  }

  async function removeFromQueue() {
    if (!selectedItem || selectedItem.status !== "queued") return;
    patchTransient(selectedItem.id, { status: "approved" });
    try {
      await removeQueueMutation.mutateAsync(Number(selectedItem.id));
      clearTransient(selectedItem.id);
      showFeedback("Removed from the publishing queue — editable again.");
    } catch {
      clearTransient(selectedItem.id);
      showFeedback("Couldn't remove this creative from the queue");
    }
  }

  function requestReturnToReview() {
    if (!selectedItem || selectedItem.status !== "approved") return;
    setReopenTarget(selectedItem);
  }

  async function confirmReturnToReview() {
    if (!reopenTarget) return;
    const target = reopenTarget;
    try {
      await reopenMutation.mutateAsync(Number(target.id));
      clearTransient(target.id);
      showFeedback("Returned to review — this creative is editable again.");
    } catch {
      showFeedback("Couldn't return this creative to review");
    } finally {
      setReopenTarget(null);
    }
  }

  function regenerate() {
    if (!selectedItem || isLocked(selectedItem)) return;
    const next = nextVariant(selectedItem.selectedVariant);
    const patch = {
      selectedVariant: next,
      templateId: VARIANT_TEMPLATE_MAP[next],
    };
    patchTransient(selectedItem.id, patch);
    scheduleSave({ ...selectedItem, ...patch });
    showFeedback("Regenerated — created a new variant of this creative.");
  }

  function generateVariants() {
    if (!selectedItem || isLocked(selectedItem)) return;
    const patch = {
      selectedVariant: "a" as const,
      templateId: "minimal" as const,
    };
    patchTransient(selectedItem.id, patch);
    scheduleSave({ ...selectedItem, ...patch });
    showFeedback("Generated four new variants to compare.");
  }

  function selectVariant(variantId: VariantId) {
    if (!selectedItem || isLocked(selectedItem)) return;
    const patch = {
      selectedVariant: variantId,
      templateId: VARIANT_TEMPLATE_MAP[variantId],
    };
    patchTransient(selectedItem.id, patch);
    scheduleSave({ ...selectedItem, ...patch });
  }

  function selectTemplate(templateId: TemplateId) {
    if (!selectedItem || isLocked(selectedItem)) return;
    const variant = variantForTemplate(templateId);
    const patch = {
      templateId,
      ...(variant ? { selectedVariant: variant } : {}),
    };
    patchTransient(selectedItem.id, patch);
    scheduleSave({ ...selectedItem, ...patch });
  }

  function updateProperties(patch: Partial<CreativeProperties>) {
    if (!selectedItem || isLocked(selectedItem)) return;
    const properties = { ...selectedItem.properties, ...patch };
    patchTransient(selectedItem.id, { properties });
    scheduleSave({ ...selectedItem, properties });
  }

  if (isLoading) {
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

      {isError ? (
        <CreativeEmptyState
          error
          onRetry={refetch}
          onGenerate={() => generateWaiting(waitingCount)}
          canGenerate={false}
        />
      ) : items.length === 0 ? (
        <CreativeEmptyState
          onGenerate={() => generateWaiting(waitingCount)}
          canGenerate={false}
        />
      ) : (
        <>
          <CreativeSummary items={items} />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(250px,1fr)_3fr]">
            <div className="order-1 flex flex-col gap-6 lg:order-none lg:col-start-2 lg:row-start-1">
              <CreativePreview item={selectedItem} />
              <VariantGallery item={selectedItem} onSelect={selectVariant} />
            </div>
            <div className="order-2 lg:order-none lg:col-start-1 lg:row-start-1">
              <CreativeQueue
                items={sorted}
                selectedId={activeSelectedId}
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
            onRemoveFromQueue={removeFromQueue}
            onReturnToReview={requestReturnToReview}
          />
        </>
      )}

      <Dialog
        open={reopenTarget !== null}
        onOpenChange={(open) => {
          if (!open) setReopenTarget(null);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Return creative to review?</DialogTitle>
            <DialogDescription>
              This will unlock the creative and allow further editing. The
              creative will need to be approved again before it can be
              published.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setReopenTarget(null)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={confirmReturnToReview}
              disabled={reopenMutation.isPending}
            >
              Return to Review
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
