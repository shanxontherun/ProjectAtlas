"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Edit, Pin, RefreshCw, Tags } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";
import { CATEGORIES_QUERY_KEY } from "./use-categories";
import {
  CategoryFormDialog,
  type CategoryFormValues,
} from "./category-form-dialog";
import { CategoryStatusBadge } from "./category-status-badge";
import { CategoryRoutesCard } from "./category-routes-card";
import { CategoriesSkeleton } from "./categories-skeleton";
import { useCategory } from "./use-categories";
import { useUpdateCategory } from "./use-categories";

export function CategoryDetailPage() {
  const params = useParams<{ categoryId: string }>();
  const categoryId = Number(params?.categoryId ?? 0);
  const queryClient = useQueryClient();
  const {
    data: category,
    isLoading,
    isError,
    error,
  } = useCategory(categoryId);
  const updateMutation = useUpdateCategory(categoryId);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function refresh() {
    await queryClient.invalidateQueries({
      queryKey: CATEGORIES_QUERY_KEY,
      refetchType: "active",
    });
  }

  async function handleSubmit(values: CategoryFormValues) {
    setFormError(null);
    try {
      await updateMutation.mutateAsync({
        name: values.name,
        slug: values.slug,
        priority: values.priority,
        dailyTarget: values.dailyTarget,
      });
      setDialogOpen(false);
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Couldn't save the category.",
      );
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-8">
        <CategoriesSkeleton />
      </div>
    );
  }

  if (isError || !category) {
    return (
      <div className="flex flex-col gap-8">
        <Button variant="ghost" size="sm" asChild className="w-fit">
          <Link href="/categories">
            <ArrowLeft data-icon="inline-start" className="size-4" />
            Back to Categories
          </Link>
        </Button>
        <EmptyState
          icon={Tags}
          title="Couldn't load this category"
          description={
            (error as Error | undefined)?.message ??
            "The category may have been removed."
          }
          action={
            <Button type="button" variant="outline" onClick={refresh}>
              Try again
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <Button variant="ghost" size="sm" asChild className="w-fit">
        <Link href="/categories">
          <ArrowLeft data-icon="inline-start" className="size-4" />
          Back to Categories
        </Link>
      </Button>

      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">
              {category.categoryName}
            </h1>
            <CategoryStatusBadge status={category.status} />
          </div>
          <p className="text-sm text-muted-foreground">
            {category.categorySlug ?? "no slug"} · Priority{" "}
            {category.priority} · {category.dailyTarget} pins/day
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={refresh}
            disabled={isLoading}
          >
            <RefreshCw data-icon="inline-start" className="size-4" />
            Refresh
          </Button>
          <Button type="button" onClick={() => setDialogOpen(true)}>
            <Edit data-icon="inline-start" className="size-4" />
            Edit Category
          </Button>
        </div>
      </header>

      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Tags className="size-4" />
          {category.activeRoutes} active route
          {category.activeRoutes === 1 ? "" : "s"}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Pin className="size-4" />
          {category.mappedBoards} board
          {category.mappedBoards === 1 ? "" : "s"}
        </span>
      </div>

      <CategoryRoutesCard categoryId={category.categoryId} />

      <CategoryFormDialog
        key={category.categoryId}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        category={category}
        submitting={updateMutation.isPending}
        error={formError}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
