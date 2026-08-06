import {
  CheckCircle2,
  Clock,
  Sparkles,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import { MetricCard } from "@/features/dashboard/metric-card";
import type { Metric } from "@/features/dashboard/types";
import { getContentCounts } from "./content-utils";
import type { ContentItem } from "./types";

const ICONS: Record<string, LucideIcon> = {
  waiting: Clock,
  generating: Sparkles,
  needs_review: TriangleAlert,
  approved: CheckCircle2,
};

type ContentSummaryProps = {
  items: ContentItem[];
};

export function ContentSummary({ items }: ContentSummaryProps) {
  const counts = getContentCounts(items);

  const metrics: Metric[] = [
    {
      id: "waiting",
      label: "Waiting",
      value: String(counts.waiting),
      delta: "Ready to generate",
      deltaTone: "neutral",
    },
    {
      id: "generating",
      label: "Generating",
      value: String(counts.generating),
      delta: "In progress",
      deltaTone: "neutral",
    },
    {
      id: "needs_review",
      label: "Needs Review",
      value: String(counts.needsReview),
      delta: "Review & approve",
      deltaTone: "attention",
    },
    {
      id: "approved",
      label: "Approved",
      value: String(counts.approved),
      delta: "Ready to queue",
      deltaTone: "positive",
    },
  ];

  return (
    <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <li key={metric.id} className="flex">
          <MetricCard metric={metric} icon={ICONS[metric.id] ?? Clock} />
        </li>
      ))}
    </ul>
  );
}
