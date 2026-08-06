import { PackagePlus, ServerCrash, SlidersHorizontal } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

type ProductEmptyStateProps = {
  variant?: "no-products" | "no-results" | "error";
  onClearFilters?: () => void;
  onRetry?: () => void;
};

export function ProductEmptyState({
  variant = "no-products",
  onClearFilters,
  onRetry,
}: ProductEmptyStateProps) {
  if (variant === "error") {
    return (
      <EmptyState
        icon={ServerCrash}
        title="Unable to load products"
        description="The product catalog could not be reached. Check that the backend service is running, then try again."
        action={
          onRetry && (
            <Button variant="outline" onClick={onRetry}>
              Try again
            </Button>
          )
        }
      />
    );
  }

  if (variant === "no-results") {
    return (
      <EmptyState
        icon={SlidersHorizontal}
        title="No products match your filters"
        description="Try adjusting your search query or clearing the active filters to see more products."
        action={
          onClearFilters && (
            <Button variant="outline" onClick={onClearFilters}>
              Clear filters
            </Button>
          )
        }
      />
    );
  }

  return (
    <EmptyState
      icon={PackagePlus}
      title="No Products Yet"
      description="Start building your Pinterest business by adding your first Amazon product."
    />
  );
}
