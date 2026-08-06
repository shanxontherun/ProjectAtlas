"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Layers, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MOCK_CONTENT_ITEMS } from "./mock-data";
import {
  expandDraft,
  filterContentItems,
  generateDraft,
  getContentCounts,
  improveDraft,
  regenerateDraft,
  shortenDraft,
} from "./content-utils";
import { ContentApproval } from "./content-approval";
import { ContentEditor } from "./content-editor";
import { ContentPreview } from "./content-preview";
import { ContentQueue } from "./content-queue";
import { ContentSkeleton } from "./content-skeleton";
import { ContentSummary } from "./content-summary";
import { ContentToolbar } from "./content-toolbar";
import type { ContentDraft, ContentItem, ContentStatusFilter, EditorAction } from "./types";

const GENERATION_DELAY = 1600;

export function ContentView() {
  const [items, setItems] = useState<ContentItem[]>(MOCK_CONTENT_ITEMS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [working, setWorking] = useState<ContentDraft | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ContentStatusFilter>("all");
  const [preview, setPreview] = useState<ContentItem | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const selectedIdRef = useRef<string | null>(null);
  const feedbackTimer = useRef<number | null>(null);
  const seed = useRef(0);

  useEffect(() => {
    const timer = window.setTimeout(() => setLoading(false), 650);
    return () => window.clearTimeout(timer);
  }, []);

  const counts = getContentCounts(items);
  const waitingCount = counts.waiting;
  const selectedItem = items.find((item) => item.id === selectedId) ?? null;
  const hasActiveFilters = query.trim() !== "" || status !== "all";

  const filtered = useMemo(
    () => filterContentItems(items, { query, status }),
    [items, query, status],
  );

  function selectItem(item: ContentItem) {
    setSelectedId(item.id);
    selectedIdRef.current = item.id;
    setWorking(item.draft ? { ...item.draft } : null);
    setFeedback(null);
  }

  function generateWaiting(limit: number) {
    const targets = items.filter((item) => item.status === "waiting").slice(0, limit);
    if (targets.length === 0) return;

    const drafts = new Map(targets.map((target) => [target.id, generateDraft(target)]));

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
    setWorking(null);
    setFeedback(null);

    targets.forEach((target) => {
      const draft = drafts.get(target.id)!;
      window.setTimeout(() => {
        setItems((current) =>
          current.map((item) =>
            item.id === target.id && item.status === "generating"
              ? { ...item, status: "needs-review", draft }
              : item,
          ),
        );
        if (selectedIdRef.current === target.id) {
          setWorking({ ...draft });
        }
      }, GENERATION_DELAY);
    });
  }

  function showFeedback(message: string) {
    setFeedback(message);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setFeedback(null), 2200);
  }

  function handleEditorAction(action: EditorAction) {
    if (!selectedItem || !working) return;

    switch (action) {
      case "copy": {
        const text = `${working.title}\n\n${working.description}\n\n${working.hashtags}\n${working.cta}`;
        navigator.clipboard?.writeText(text).catch(() => undefined);
        showFeedback("Copied to clipboard");
        break;
      }
      case "improve":
        setWorking(improveDraft(working));
        showFeedback("Improved — added a stronger closer");
        break;
      case "regenerate":
        seed.current += 1;
        setWorking(regenerateDraft(working, seed.current));
        showFeedback("Regenerated — new variant created");
        break;
      case "shorten":
        setWorking(shortenDraft(working));
        showFeedback("Shortened — trimmed to the essentials");
        break;
      case "expand":
        seed.current += 1;
        setWorking(expandDraft(working, seed.current));
        showFeedback("Expanded — added more detail");
        break;
      case "reset":
        if (selectedItem.draft) setWorking({ ...selectedItem.draft });
        showFeedback("Reset to the generated draft");
        break;
    }
  }

  function commitStatus(itemId: string, patch: Partial<ContentItem>) {
    setItems((current) =>
      current.map((item) => (item.id === itemId ? { ...item, ...patch } : item)),
    );
  }

  function approveItem() {
    if (!selectedItem || !working) return;
    commitStatus(selectedItem.id, {
      status: "approved",
      draft: { ...working },
      hasChanges: false,
    });
  }

  function requestChanges() {
    if (!selectedItem || !working) return;
    commitStatus(selectedItem.id, {
      status: "needs-review",
      draft: { ...working },
      hasChanges: true,
    });
  }

  function queueItem() {
    if (!selectedItem || !working) return;
    commitStatus(selectedItem.id, {
      status: "queued",
      draft: { ...working },
      hasChanges: false,
    });
  }

  function clearFilters() {
    setQuery("");
    setStatus("all");
  }

  if (loading) {
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
          readOnly={selectedItem?.status === "queued"}
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

      <ContentPreview item={preview} onClose={() => setPreview(null)} />
    </div>
  );
}
