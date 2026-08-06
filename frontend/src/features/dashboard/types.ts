export type MetricTone = "positive" | "attention" | "neutral";

export type Metric = {
  id: string;
  label: string;
  value: string;
  delta?: string;
  deltaTone?: MetricTone;
};

export type FocusPriority = "low" | "medium" | "high";

export type FocusItem = {
  id: string;
  label: string;
  count: number;
  priority: FocusPriority;
  actionLabel: string;
  href: string;
};

export type ActivityIcon =
  | "image"
  | "ai"
  | "publish"
  | "import"
  | "category"
  | "check";

export type ActivityItem = {
  id: string;
  icon: ActivityIcon;
  title: string;
  description: string;
  time: string;
};

export type PipelineStageKey =
  | "imported"
  | "research"
  | "ai"
  | "creative"
  | "publishing"
  | "live";

export type PipelineStage = {
  key: PipelineStageKey;
  label: string;
  count: number;
};

export type CategoryPerformance = {
  id: string;
  name: string;
  products: number;
  ready: number;
};

export type QuickAction = {
  id: string;
  title: string;
  description: string;
  href: string;
  count?: number;
};

export type SystemService = {
  id: string;
  label: string;
  statusLabel: string;
};

export type DashboardData = {
  welcome: {
    subtitle: string;
  };
  metrics: Metric[];
  focus: FocusItem[];
  activity: ActivityItem[];
  pipeline: PipelineStage[];
  categories: CategoryPerformance[];
  quickActions: QuickAction[];
  services: SystemService[];
};
