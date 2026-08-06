import { PackagePlus, SlidersHorizontal } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

type ProductEmptyStateProps = {
  variant?: "no-products" | "no-results";
  onClearFilters?: () => void;
};

export function ProductEmptyState({
  variant = "no-products",
  onClearFilters,
}: ProductEmptyStateProps) {
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
