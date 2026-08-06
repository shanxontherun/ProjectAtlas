"use client";

import { useEffect, useState } from "react";
import { MOCK_DASHBOARD } from "./mock-data";
import { ActivityFeed } from "./activity-feed";
import { CategoryPerformance } from "./category-performance";
import { DashboardEmptyState } from "./dashboard-empty-state";
import { DashboardSkeleton } from "./dashboard-skeleton";
import { ExecutiveMetrics } from "./executive-metrics";
import { PipelineOverview } from "./pipeline-overview";
import { QuickActions } from "./quick-actions";
import { SystemHealth } from "./system-health";
import { TodayFocus } from "./today-focus";
import { WelcomeHeader } from "./welcome-header";

export function DashboardPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => setLoading(false), 650);
    return () => window.clearTimeout(timer);
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  const hasData =
    MOCK_DASHBOARD.metrics.length > 0 ||
    MOCK_DASHBOARD.pipeline.some((stage) => stage.count > 0);

  if (!hasData) {
    return <DashboardEmptyState />;
  }

  return (
    <div className="flex flex-col gap-8">
      <WelcomeHeader subtitle={MOCK_DASHBOARD.welcome.subtitle} />
      <ExecutiveMetrics metrics={MOCK_DASHBOARD.metrics} />
      <TodayFocus items={MOCK_DASHBOARD.focus} />
      <ActivityFeed items={MOCK_DASHBOARD.activity} />
      <PipelineOverview stages={MOCK_DASHBOARD.pipeline} />
      <CategoryPerformance categories={MOCK_DASHBOARD.categories} />
      <QuickActions actions={MOCK_DASHBOARD.quickActions} />
      <SystemHealth services={MOCK_DASHBOARD.services} />
    </div>
  );
}
