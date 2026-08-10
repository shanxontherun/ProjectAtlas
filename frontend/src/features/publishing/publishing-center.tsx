"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  defaultScheduleTime,
  formatPublishTime,
  getPublishCounts,
  sortPublications,
  sortQueue,
  toDatetimeLocal,
} from "./publishing-utils";
import {
  mapBoard,
  mapPublication,
  mapPublishItem,
} from "./publishing-api";
import {
  usePublishNow,
  usePublishing,
  useSchedulePin,
  useUpdatePinBoard,
} from "./use-publishing";
import { PublishedHistory } from "./published-history";
import { PublishConsole } from "./publish-console";
import { PublishingQueue } from "./publishing-queue";
import { PublishingSkeleton } from "./publishing-skeleton";
import { PublishingSummary } from "./publishing-summary";
import type {
  Publication,
  PublishItem,
  PublishTimingMode,
} from "./types";

export function PublishingCenter() {
  const { data, isLoading, isError, error } = usePublishing();
  const scheduleMutation = useSchedulePin();
  const publishMutation = usePublishNow();
  const boardMutation = useUpdatePinBoard();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [timingMode, setTimingMode] = useState<PublishTimingMode>("now");
  const [scheduleValue, setScheduleValue] = useState(() =>
    toDatetimeLocal(defaultScheduleTime()),
  );
  const [feedback, setFeedback] = useState<string | null>(null);
  const [actionPending, setActionPending] = useState(false);

  const feedbackTimer = useRef<number | null>(null);

  const queue: PublishItem[] = useMemo(
    () => (data?.queue ?? []).map(mapPublishItem),
    [data],
  );

  const publications: Publication[] = useMemo(
    () => (data?.history ?? []).map(mapPublication),
    [data],
  );

  const boards = useMemo(
    () => (data?.boards ?? []).map(mapBoard),
    [data],
  );

  const boardById = useMemo(
    () => new Map(boards.map((board) => [board.id, board])),
    [boards],
  );

  const hasRealAccount = useMemo(
    () => (data?.accounts ?? []).some((account) => !account.is_seed),
    [data],
  );

  function showFeedback(message: string) {
    setFeedback(message);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setFeedback(null), 2600);
  }

  function reflectPlan(item: PublishItem) {
    if (item.status === "scheduled" && item.scheduledAt) {
      setTimingMode("schedule");
      setScheduleValue(toDatetimeLocal(new Date(item.scheduledAt)));
    }
  }

  function selectItem(item: PublishItem) {
    setSelectedId(item.id);
    setFeedback(null);
    reflectPlan(item);
  }

  useEffect(() => {
    if (!isLoading && queue.length > 0 && selectedId === null) {
      const first = sortQueue(queue)[0];
      const timer = window.setTimeout(() => {
        setSelectedId(first.id);
        reflectPlan(first);
      }, 0);
      return () => window.clearTimeout(timer);
    }
  }, [isLoading, queue, selectedId]);

  const selectedItem =
    queue.find((item) => item.id === selectedId) ?? null;

  const now = new Date();
  const scheduleDate = new Date(scheduleValue);
  const scheduleValid =
    !Number.isNaN(scheduleDate.getTime()) &&
    scheduleDate.getTime() > now.getTime();
  const scheduleInvalid =
    timingMode === "schedule" && scheduleValue !== "" && !scheduleValid;
  const canSchedule =
    selectedItem !== null &&
    selectedItem.boardId !== null &&
    timingMode === "schedule" &&
    scheduleValid &&
    !actionPending;

  async function updateBoard(boardId: string) {
    if (!selectedItem) return;
    const board = boardById.get(boardId);
    if (!board) return;
    const boardRow = data?.boards.find(
      (candidate) => candidate.board_id === Number(boardId),
    );
    if (!boardRow) return;
    const pinId = Number(selectedItem.id);

    setActionPending(true);
    try {
      await boardMutation.mutateAsync({
        pinId,
        accountId: boardRow.account_id,
        boardId: boardRow.board_id,
      });
      showFeedback(`Destination set to ${board.name}`);
    } catch {
      showFeedback("Couldn't update the pin board");
    } finally {
      setActionPending(false);
    }
  }

  function boardNameFor(item: PublishItem) {
    return item.boardId
      ? (boardById.get(item.boardId)?.name ?? "Pinterest")
      : "Pinterest";
  }

  async function publishNowAction() {
    if (!selectedItem) return;
    const item = selectedItem;
    const boardName = boardNameFor(item);
    const pinId = Number(item.id);

    setActionPending(true);
    try {
      await publishMutation.mutateAsync(pinId);
      showFeedback(`Published to ${boardName}`);
    } catch (publishError) {
      const detail =
        publishError instanceof Error
          ? publishError.message
          : "Couldn't publish this pin";
      showFeedback(detail);
    } finally {
      setActionPending(false);
    }
  }

  async function schedulePublish() {
    if (!selectedItem || !canSchedule) return;
    const item = selectedItem;
    const scheduledAt = scheduleDate.toISOString();

    setActionPending(true);
    try {
      await scheduleMutation.mutateAsync({
        pinId: Number(item.id),
        scheduledAt,
      });
      showFeedback(`Scheduled for ${formatPublishTime(scheduledAt)}`);
    } catch {
      showFeedback("Couldn't schedule this pin");
    } finally {
      setActionPending(false);
    }
  }

  async function downloadPin() {
    if (!selectedItem || selectedItem.creativeId === null) return;
    const creativeId = selectedItem.creativeId;
    setActionPending(true);
    try {
      const response = await fetch(`/api/publishing/download/${creativeId}`);
      if (!response.ok) {
        throw new Error(`Download failed (${response.status})`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${selectedItem.productName.replace(/\s+/g, "-").toLowerCase()}.png`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      showFeedback("Pin image downloaded.");
    } catch {
      showFeedback("Couldn't download the pin image");
    } finally {
      setActionPending(false);
    }
  }

  if (isLoading) {
    return <PublishingSkeleton />;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed bg-card/50 px-6 py-16 text-center">
        <p className="text-sm font-semibold tracking-tight">
          Couldn&apos;t load the Publishing Center
        </p>
        <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
          {(error as Error | undefined)?.message ??
            "The publishing API did not respond."}
        </p>
        <Button asChild variant="outline">
          <Link href="/publishing">Try again</Link>
        </Button>
      </div>
    );
  }

  const counts = getPublishCounts(queue, publications);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            Publishing Center
          </h1>
          <p className="text-sm text-muted-foreground">
            Review approved creatives, pick a board and time, and send pins to
            Pinterest.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/creatives">
            <ImageIcon data-icon="inline-start" className="size-4" />
            Review Creatives
          </Link>
        </Button>
      </header>

      <PublishingSummary
        counts={counts}
        boardsCount={data?.summary.boards ?? boards.length}
        hasRealAccount={hasRealAccount}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
        <PublishingQueue
          items={sortQueue(queue)}
          selectedId={selectedId}
          onSelect={selectItem}
        />
        <PublishConsole
          item={selectedItem}
          boards={boards}
          timingMode={timingMode}
          scheduleValue={scheduleValue}
          canSchedule={canSchedule}
          scheduleInvalid={scheduleInvalid}
          hasRealAccount={hasRealAccount}
          onTimingChange={setTimingMode}
          onScheduleChange={setScheduleValue}
          onSelectBoard={updateBoard}
          onPublishNow={publishNowAction}
          onSchedule={schedulePublish}
          onDownload={downloadPin}
          feedback={feedback}
        />
      </div>

      <PublishedHistory publications={sortPublications(publications)} />
    </div>
  );
}
