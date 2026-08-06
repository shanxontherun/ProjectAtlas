import { ServerCrash } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

type ContentEmptyStateProps = {
  onRetry: () => void;
};

export function ContentEmptyState({ onRetry }: ContentEmptyStateProps) {
  return (
    <EmptyState
      icon={ServerCrash}
      title="Unable to load AI content"
      description="The AI Studio could not reach the backend. Check that the backend service is running, then try again."
      action={
        <Button variant="outline" onClick={onRetry}>
          Try again
        </Button>
      }
    />
  );
}
