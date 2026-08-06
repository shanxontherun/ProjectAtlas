"use client";

import { useMemo, useRef, useState } from "react";
import { Layers, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  expandDraft,
  filterContentItems,
  getContentCounts,
  improveDraft,
  shortenDraft,
} from "./content-utils";
import { mapAiContent } from "./content-api";
import { ContentApproval } from "./content-approval";
import { ContentEditor } from "./content-editor";
import { ContentEmptyState } from "./content-empty-state";
import { ContentPreview } from "./content-preview";
import { ContentQueue } from "./content-queue";
import { ContentSkeleton } from "./content-skeleton";
import { ContentSummary } from "./content-summary";
import { ContentToolbar } from "./content-toolbar";
import {
  useApproveContent,
  useContent,
  useGenerateContent,
} from "./use-content";
import type {
  ContentDraft,
  ContentItem,
  ContentStatusFilter,
  EditorAction,
} from "./types";

type TransientPatch = {
  status: ContentItem["status"];
  draft?: ContentDraft | null;
  hasChanges?: boolean;
};

export function ContentView() {
  const {
    data: serverItems = [],
    isLoading,
    isError,
    refetch,
  } = useContent();

  const generateMutation = useGenerateContent();
  const approveMutation = useApproveContent();

  // Transient presentation states (generating / queued / needs-changes)
  // live only in the browser; the backend always wins on the next fetch.
  const [transient, setTransient] = useState<
    Record<string, TransientPatch>
  >({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [working, setWorking] = useState<ContentDraft | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ContentStatusFilter>("all");
  const [preview, setPreview] = useState<ContentItem | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const feedbackTimer = useRef<number | null>(null);
  const seed = useRef(0);

  const items = useMemo(
    () =>
      serverItems.map((item) => {
        const patch = transient[item.id];
        if (!patch) return item;
        if (patch.status === "generating" && item.draft) return item;
        return {
          ...item,
          status: patch.status,
          ...(patch.draft !== undefined ? { draft: patch.draft } : {}),
          ...(patch.hasChanges !== undefined
            ? { hasChanges: patch.hasChanges }
            : {}),
        };
      }),
    [serverItems, transient],
  );

  const selectedItem = items.find((item) => item.id === selectedId) ?? null;

  // The editor buffer falls back to the server draft, so a freshly
  // generated or refetched draft appears without a manual sync.
  const effectiveDraft = working ?? selectedItem?.draft ?? null;

  const counts = getContentCounts(items);
  const waitingCount = counts.waiting;
  const hasActiveFilters = query.trim() !== "" || status !== "all";

  const filtered = useMemo(
    () => filterContentItems(items, { query, status }),
    [items, query, status],
  );

  function selectItem(item: ContentItem) {
    setSelectedId(item.id);
    setWorking(item.draft ? { ...item.draft } : null);
    setFeedback(null);
  }

  function patchTransient(itemId: string, patch: TransientPatch) {
    setTransient((current) => ({ ...current, [itemId]: patch }));
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

  async function generateWaiting(limit: number) {
    const targets = items
      .filter((item) => item.status === "waiting")
      .slice(0, limit);
    if (targets.length === 0) return;

    const first = targets[0];
    setSelectedId(first.id);
    setWorking(null);
    setFeedback(null);

    targets.forEach((target) => {
      patchTransient(target.id, { status: "generating", draft: null });
    });

    for (const target of targets) {
      try {
        await generateMutation.mutateAsync(Number(target.id));
      } catch {
        clearTransient(target.id);
        showFeedback(`Couldn't generate content for ${target.productName}`);
      }
    }
  }

  async function handleEditorAction(action: EditorAction) {
    if (!selectedItem || !effectiveDraft) return;

    switch (action) {
      case "copy": {
        const text = `${effectiveDraft.title}\n\n${effectiveDraft.description}\n\n${effectiveDraft.hashtags}\n${effectiveDraft.cta}`;
        navigator.clipboard?.writeText(text).catch(() => undefined);
        showFeedback("Copied to clipboard");
        break;
      }
      case "improve":
        setWorking(improveDraft(effectiveDraft));
        showFeedback("Improved — added a stronger closer");
        break;
      case "regenerate":
        if (!selectedItem || !selectedItem.draft) return;
        // Manual regeneration is a real backend round-trip: the existing
        // ai_content row is replaced in place (never appended), the query
        // invalidates, and the editor buffer picks up the returned content.
        patchTransient(selectedItem.id, {
          status: "generating",
          draft: null,
        });
        try {
          const result = await generateMutation.mutateAsync(
            Number(selectedItem.id),
          );
          const updated = result.content
            ? mapAiContent(result.content)
            : null;
          setWorking(updated?.draft ? { ...updated.draft } : null);
          clearTransient(selectedItem.id);
          showFeedback("Regenerated — fresh content ready");
        } catch {
          clearTransient(selectedItem.id);
          showFeedback("Couldn't regenerate this content");
        }
        break;
      case "shorten":
        setWorking(shortenDraft(effectiveDraft));
        showFeedback("Shortened — trimmed to the essentials");
        break;
      case "expand":
        seed.current += 1;
        setWorking(expandDraft(effectiveDraft, seed.current));
        showFeedback("Expanded — added more detail");
        break;
      case "reset":
        if (selectedItem.draft) setWorking({ ...selectedItem.draft });
        showFeedback("Reset to the generated draft");
        break;
    }
  }

  async function approveItem() {
    if (!selectedItem || !effectiveDraft) return;
    patchTransient(selectedItem.id, { status: "approved" });
    try {
      await approveMutation.mutateAsync(Number(selectedItem.id));
    } catch {
      clearTransient(selectedItem.id);
      showFeedback("Couldn't approve this content");
    }
  }

  function requestChanges() {
    if (!selectedItem || !effectiveDraft) return;
    patchTransient(selectedItem.id, {
      status: "needs-review",
      draft: { ...effectiveDraft },
      hasChanges: true,
    });
  }

  function queueItem() {
    if (!selectedItem || !effectiveDraft) return;
    patchTransient(selectedItem.id, {
      status: "queued",
      draft: { ...effectiveDraft },
      hasChanges: false,
    });
  }

  function clearFilters() {
    setQuery("");
    setStatus("all");
  }

  if (isLoading) {
    return <ContentSkeleton />;
  }

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">AI Studio</h1>
          <p className="text-sm text-muted-foreground">
            Generate, review and approve Pinterest-ready content.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => generateWaiting(1)} disabled={waitingCount === 0}>
            <Sparkles data-icon="inline-start" className="size-4" />
            Generate AI Content
          </Button>
          <Button
            variant="outline"
            onClick={() => generateWaiting(waitingCount)}
            disabled={waitingCount === 0}
          >
            <Layers data-icon="inline-start" className="size-4" />
            Bulk Generate
          </Button>
        </div>
      </header>

      {isError ? (
        <ContentEmptyState onRetry={refetch} />
      ) : (
        <>
          <ContentSummary items={items} />

          <ContentToolbar
            query={query}
            onQueryChange={setQuery}
            status={status}
            onStatusChange={setStatus}
            total={items.length}
            shown={filtered.length}
          />

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
            <ContentQueue
              items={filtered}
              selectedId={selectedId}
              onSelect={selectItem}
              onPreview={setPreview}
              hasActiveFilters={hasActiveFilters}
              onClearFilters={clearFilters}
            />
            <ContentEditor
              item={selectedItem}
              draft={working}
              readOnly={
                selectedItem?.status === "queued" ||
                generateMutation.isPending
              }
              feedback={feedback}
              onDraftChange={setWorking}
              onAction={handleEditorAction}
              onPreview={() => setPreview(selectedItem)}
            />
          </div>

          <ContentApproval
            item={selectedItem}
            onApprove={approveItem}
            onNeedsChanges={requestChanges}
            onQueue={queueItem}
          />
        </>
      )}

      <ContentPreview item={preview} onClose={() => setPreview(null)} />
    </div>
  );
}
