import { ImagePlay } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

type CreativeEmptyStateProps = {
  onGenerate: () => void;
  canGenerate: boolean;
};

export function CreativeEmptyState({
  onGenerate,
  canGenerate,
}: CreativeEmptyStateProps) {
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
