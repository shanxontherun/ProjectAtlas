import { Badge } from "@/components/ui/badge";
import type { CategoryStatus } from "./types";

export function CategoryStatusBadge({
  status,
}: {
  status: CategoryStatus;
}) {
  if (status === "INACTIVE") {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        Archived
      </Badge>
    );
  }

  return <Badge variant="secondary">Active</Badge>;
}
