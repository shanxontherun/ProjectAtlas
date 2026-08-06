import Link from "next/link";
import { LayoutDashboard } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

export function DashboardEmptyState() {
  return (
    <EmptyState
      icon={LayoutDashboard}
      title="All clear — nothing to show yet"
      description="Once your product pipeline starts running, you'll see key metrics, today's focus, recent activity, and system health here."
      action={
        <Button asChild>
          <Link href="/products">Browse products</Link>
        </Button>
      }
    />
  );
}
