"use client";

import { CalendarClock, Download, LayoutGrid, Send, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ProductImage } from "@/features/products/product-image";
import { CreativePin } from "@/features/creatives/creative-preview";
import { TEMPLATE_BY_ID } from "@/features/creatives/mock-data";
import { formatCount } from "./publishing-utils";
import { PublishingStatusBadge } from "./publishing-status-badge";
import type {
  PinterestBoard,
  PublishItem,
  PublishTimingMode,
} from "./types";

type PublishConsoleProps = {
  item: PublishItem | null;
  boards: PinterestBoard[];
  timingMode: PublishTimingMode;
  scheduleValue: string;
  canSchedule: boolean;
  scheduleInvalid: boolean;
  hasRealAccount: boolean;
  onTimingChange: (mode: PublishTimingMode) => void;
  onScheduleChange: (value: string) => void;
  onSelectBoard: (boardId: string) => void;
  onPublishNow: () => void;
  onSchedule: () => void;
  onDownload: () => void;
  feedback: string | null;
};

export function PublishConsole({
  item,
  boards,
  timingMode,
  scheduleValue,
  canSchedule,
  scheduleInvalid,
  hasRealAccount,
  onTimingChange,
  onScheduleChange,
  onSelectBoard,
  onPublishNow,
  onSchedule,
  onDownload,
  feedback,
}: PublishConsoleProps) {
  if (!item) {
    return (
      <section className="flex min-h-[30rem] items-center justify-center rounded-xl border border-dashed bg-card/50 px-6 py-16 text-center">
        <div className="space-y-2">
          <p className="text-sm font-semibold tracking-tight">
            Select a pin from the queue
          </p>
          <p className="mx-auto max-w-sm text-sm leading-relaxed text-muted-foreground">
            Pick a board and a time, then publish it now or schedule it.
          </p>
        </div>
      </section>
    );
  }

  const template = TEMPLATE_BY_ID[item.templateId];

  return (
    <section className="flex flex-col gap-5 rounded-xl border border-border bg-card p-5">
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
        <PublishingStatusBadge status={item.status} />
      </header>

      <div className="flex justify-center rounded-xl bg-muted/40 px-6 py-6">
        <div className="w-full max-w-[16rem]">
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

      <div className="space-y-2.5">
        <div className="flex items-center justify-between gap-2">
          <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <LayoutGrid data-icon="inline-start" className="size-3.5" />
            Pinterest Board
          </span>
          <span className="text-xs text-muted-foreground">
            {item.boardId ? "Destination set" : "Select a board"}
          </span>
        </div>
        <div
          role="group"
          aria-label="Choose a Pinterest board"
          className="grid grid-cols-2 gap-2"
        >
          {boards.map((board) => {
            const selected = item.boardId === board.id;

            return (
              <button
                key={board.id}
                type="button"
                aria-pressed={selected}
                onClick={() => onSelectBoard(board.id)}
                className={cn(
                  "flex flex-col items-start gap-1 rounded-lg border p-2.5 text-left outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50",
                  selected
                    ? "border-primary bg-muted ring-1 ring-ring/40"
                    : "border-border hover:bg-muted/50",
                )}
              >
                <span
                  className={cn(
                    "w-full truncate text-xs font-medium",
                    selected ? "text-foreground" : "text-foreground/80",
                  )}
                >
                  {board.name}
                </span>
                <span className="text-[0.7rem] tabular-nums text-muted-foreground">
                  {formatCount(board.pinCount)} pins ·{" "}
                  {formatCount(board.followerCount)} followers
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-2.5">
        <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          <CalendarClock data-icon="inline-start" className="size-3.5" />
          Publish Time
        </div>
        <div
          role="group"
          aria-label="Choose publish timing"
          className="inline-flex items-center rounded-lg bg-muted p-[3px]"
        >
          <button
            type="button"
            aria-pressed={timingMode === "now"}
            onClick={() => onTimingChange("now")}
            className={cn(
              "inline-flex h-7 items-center gap-1.5 rounded-md px-2.5 text-sm font-medium transition-all",
              timingMode === "now"
                ? "bg-background text-foreground shadow-sm dark:bg-input/30"
                : "text-foreground/60 hover:text-foreground dark:text-muted-foreground dark:hover:text-foreground",
            )}
          >
            <Zap data-icon="inline-start" className="size-3.5" />
            Publish now
          </button>
          <button
            type="button"
            aria-pressed={timingMode === "schedule"}
            onClick={() => onTimingChange("schedule")}
            className={cn(
              "inline-flex h-7 items-center gap-1.5 rounded-md px-2.5 text-sm font-medium transition-all",
              timingMode === "schedule"
                ? "bg-background text-foreground shadow-sm dark:bg-input/30"
                : "text-foreground/60 hover:text-foreground dark:text-muted-foreground dark:hover:text-foreground",
            )}
          >
            <CalendarClock data-icon="inline-start" className="size-3.5" />
            Schedule
          </button>
        </div>

        {timingMode === "schedule" && (
          <div className="space-y-1.5">
            <Input
              type="datetime-local"
              value={scheduleValue}
              aria-label="Scheduled publish time"
              aria-invalid={scheduleInvalid}
              onChange={(event) => onScheduleChange(event.target.value)}
            />
            <p
              className={cn(
                "text-xs",
                scheduleInvalid
                  ? "font-medium text-red-600 dark:text-red-400"
                  : "text-muted-foreground",
              )}
            >
              {scheduleInvalid
                ? "Choose a time in the future."
                : "This pin will publish to the selected board at this time."}
            </p>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t pt-4">
        <Button
          type="button"
          onClick={onPublishNow}
          disabled={!hasRealAccount}
          title={
            hasRealAccount
              ? "Publish this pin now"
              : "Connect a Pinterest account before publishing"
          }
        >
          <Send data-icon="inline-start" className="size-4" />
          Publish Now
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={timingMode !== "schedule" || !canSchedule}
          onClick={onSchedule}
        >
          <CalendarClock data-icon="inline-start" className="size-4" />
          Schedule
        </Button>
        <Button
          type="button"
          variant="ghost"
          disabled={item.creativeId === null}
          onClick={onDownload}
          title="Download the pin image"
        >
          <Download data-icon="inline-start" className="size-4" />
          Download Pin
        </Button>
      </div>

      {!hasRealAccount && (
        <p className="-mt-2 text-xs font-medium text-muted-foreground">
          Connect a Pinterest account before publishing.
        </p>
      )}

      {feedback && (
        <p className="-mt-2 text-xs font-medium text-primary">{feedback}</p>
      )}
    </section>
  );
}
