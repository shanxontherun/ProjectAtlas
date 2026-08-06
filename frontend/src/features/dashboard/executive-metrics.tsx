import {
  CheckCircle2,
  ImageIcon,
  ListChecks,
  Package,
  Send,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { MetricCard } from "./metric-card";
import type { Metric } from "./types";

const METRIC_ICONS: Record<string, LucideIcon> = {
  products: Package,
  ai_content: Sparkles,
  creatives: ImageIcon,
  published: Send,
  success_rate: CheckCircle2,
  ready_today: ListChecks,
};

type ExecutiveMetricsProps = {
  metrics: Metric[];
};

export function ExecutiveMetrics({ metrics }: ExecutiveMetricsProps) {
  return (
    <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((metric) => (
        <li key={metric.id} className="flex">
          <MetricCard metric={metric} icon={METRIC_ICONS[metric.id] ?? Package} />
        </li>
      ))}
    </ul>
  );
}
