import {
  CalendarClock,
  CheckCircle2,
  LayoutGrid,
  Send,
  type LucideIcon,
} from "lucide-react";
import { MetricCard } from "@/features/dashboard/metric-card";
import type { Metric } from "@/features/dashboard/types";
import type { PublishCounts } from "./publishing-utils";

const ICONS: Record<string, LucideIcon> = {
  ready: Send,
  scheduled: CalendarClock,
  published: CheckCircle2,
  boards: LayoutGrid,
};

type PublishingSummaryProps = {
  counts: PublishCounts;
  boardsCount: number;
};

export function PublishingSummary({
  counts,
  boardsCount,
}: PublishingSummaryProps) {
  const metrics: Metric[] = [
    {
      id: "ready",
      label: "Ready to Publish",
      value: String(counts.ready),
      delta:
        counts.ready > 0
          ? "Creatives approved & queued"
          : "Queue is clear",
      deltaTone: counts.ready > 0 ? "attention" : "positive",
    },
    {
      id: "scheduled",
      label: "Scheduled",
      value: String(counts.scheduled),
      delta: "Upcoming pins",
      deltaTone: "neutral",
    },
    {
      id: "published",
      label: "Published",
      value: String(counts.published),
      delta: "Across your boards",
      deltaTone: "positive",
    },
    {
      id: "boards",
      label: "Boards",
      value: String(boardsCount),
      delta: "Connected to Pinterest",
      deltaTone: "positive",
    },
  ];

  return (
    <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <li key={metric.id} className="flex">
          <MetricCard metric={metric} icon={ICONS[metric.id] ?? Send} />
        </li>
      ))}
    </ul>
  );
}
