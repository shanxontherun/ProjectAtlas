import { ImagePlay, ServerCrash } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

type CreativeEmptyStateProps = {
  onGenerate: () => void;
  canGenerate: boolean;
  error?: boolean;
  onRetry?: () => void;
};

export function CreativeEmptyState({
  onGenerate,
  canGenerate,
  error = false,
  onRetry,
}: CreativeEmptyStateProps) {
  if (error) {
    return (
      <EmptyState
        icon={ServerCrash}
        title="Unable to load creatives"
        description="Creative Studio could not reach the backend. Check that the backend service is running, then try again."
        action={
          <Button variant="outline" onClick={onRetry}>
            Try again
          </Button>
        }
      />
    );
  }

  return (
    <EmptyState
      icon={ImagePlay}
      title="No creatives waiting for review"
      description="Products with approved content will appear here once Atlas generates their Pinterest creatives. Generate creatives now to start the review flow."
      action={
        <Button onClick={onGenerate} disabled={!canGenerate}>
          Generate Creatives
        </Button>
      }
    />
  );
}
