"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  BOARD_BY_ID,
  MOCK_BOARDS,
  MOCK_PUBLICATIONS,
  MOCK_PUBLISH_QUEUE,
} from "./mock-data";
import {
  defaultScheduleTime,
  formatPublishTime,
  getPublishCounts,
  sortPublications,
  sortQueue,
  toDatetimeLocal,
} from "./publishing-utils";
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
  const [queue, setQueue] = useState<PublishItem[]>(MOCK_PUBLISH_QUEUE);
  const [publications, setPublications] =
    useState<Publication[]>(MOCK_PUBLICATIONS);
  const [selectedId, setSelectedId] = useState<string | null>(
    () => MOCK_PUBLISH_QUEUE[0]?.id ?? null,
  );
  const [loading, setLoading] = useState(true);
  const [timingMode, setTimingMode] = useState<PublishTimingMode>("now");
  const [scheduleValue, setScheduleValue] = useState(() =>
    toDatetimeLocal(defaultScheduleTime()),
  );
  const [feedback, setFeedback] = useState<string | null>(null);

  const feedbackTimer = useRef<number | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setLoading(false), 650);
    return () => window.clearTimeout(timer);
  }, []);

  const selectedItem = queue.find((item) => item.id === selectedId) ?? null;

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
    scheduleValid;

  function showFeedback(message: string) {
    setFeedback(message);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setFeedback(null), 2200);
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

  function selectNext(remaining: PublishItem[]) {
    const next = remaining[0] ?? null;
    setSelectedId(next?.id ?? null);
    if (next) reflectPlan(next);
  }

  function updateBoard(boardId: string) {
    if (!selectedItem) return;
    setQueue((current) =>
      current.map((item) =>
        item.id === selectedItem.id ? { ...item, boardId } : item,
      ),
    );
  }

  function boardNameFor(item: PublishItem) {
    return item.boardId ? (BOARD_BY_ID[item.boardId]?.name ?? "Pinterest") : "Pinterest";
  }

  function publishNow() {
    if (!selectedItem) return;
    const item = selectedItem;
    const boardName = boardNameFor(item);

    const publication: Publication = {
      id: `pub_${Date.now()}`,
      productName: item.productName,
      category: item.category,
      imageUrl: item.imageUrl,
      boardName,
      status: "published",
      eventAt: new Date().toISOString(),
    };

    const remaining = queue.filter((entry) => entry.id !== item.id);
    setQueue(remaining);
    setPublications((current) => [publication, ...current]);
    selectNext(remaining);
    showFeedback(`Published to ${boardName}`);
  }

  function schedulePublish() {
    if (!selectedItem || !canSchedule) return;
    const item = selectedItem;
    const scheduledAt = scheduleDate.toISOString();
    const boardName = boardNameFor(item);

    const publication: Publication = {
      id: `pub_${Date.now()}`,
      productName: item.productName,
      category: item.category,
      imageUrl: item.imageUrl,
      boardName,
      status: "scheduled",
      eventAt: scheduledAt,
    };

    const remaining = queue.filter((entry) => entry.id !== item.id);
    setQueue(remaining);
    setPublications((current) => [publication, ...current]);
    selectNext(remaining);
    showFeedback(`Scheduled for ${formatPublishTime(scheduledAt)}`);
  }

  if (loading) {
    return <PublishingSkeleton />;
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
        boardsCount={MOCK_BOARDS.length}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
        <PublishingQueue
          items={sortQueue(queue)}
          selectedId={selectedId}
          onSelect={selectItem}
        />
        <PublishConsole
          item={selectedItem}
          boards={MOCK_BOARDS}
          timingMode={timingMode}
          scheduleValue={scheduleValue}
          canSchedule={canSchedule}
          scheduleInvalid={scheduleInvalid}
          onTimingChange={setTimingMode}
          onScheduleChange={setScheduleValue}
          onSelectBoard={updateBoard}
          onPublishNow={publishNow}
          onSchedule={schedulePublish}
          feedback={feedback}
        />
      </div>

      <PublishedHistory publications={sortPublications(publications)} />
    </div>
  );
}
