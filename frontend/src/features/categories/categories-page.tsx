"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CalendarClock,
  Layers,
  Package,
  Plus,
  RefreshCw,
  Tags,
  Users,
} from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";
import { cn } from "@/lib/utils";
import { CATEGORIES_QUERY_KEY, useCategories } from "./use-categories";
import { createCategory, setCategoryStatus, updateCategory } from "./categories-api";
import {
  CategoryFormDialog,
  type CategoryFormValues,
} from "./category-form-dialog";
import { CategoryStatusBadge } from "./category-status-badge";
import { CategoriesSkeleton } from "./categories-skeleton";
import type { Category, CategoryInput } from "./types";

export function CategoriesPage() {
  const { data: categories = [], isLoading, isError, error } = useCategories();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<Category | null>(null);
  const [restoreTarget, setRestoreTarget] = useState<Category | null>(null);

  function invalidate() {
    queryClient.invalidateQueries({
      queryKey: CATEGORIES_QUERY_KEY,
      refetchType: "active",
    });
  }

  const createMutation = useMutation({
    mutationFn: (input: CategoryInput) => createCategory(input),
    onSuccess: invalidate,
  });

  const updateMutation = useMutation({
    mutationFn: (args: { categoryId: number; input: Partial<CategoryInput> }) =>
      updateCategory(args.categoryId, args.input),
    onSuccess: invalidate,
  });

  const statusMutation = useMutation({
    mutationFn: (args: { categoryId: number; status: "ACTIVE" | "INACTIVE" }) =>
      setCategoryStatus(args.categoryId, args.status),
    onSuccess: invalidate,
  });

  async function refresh() {
    await queryClient.invalidateQueries({
      queryKey: CATEGORIES_QUERY_KEY,
      refetchType: "active",
    });
  }

  function openCreate() {
    setEditing(null);
    setFormError(null);
    setDialogOpen(true);
  }

  function openEdit(category: Category) {
    setEditing(category);
    setFormError(null);
    setDialogOpen(true);
  }

  async function handleSubmit(values: CategoryFormValues) {
    setFormError(null);

    try {
      if (editing) {
        await updateMutation.mutateAsync({
          categoryId: editing.categoryId,
          input: {
            name: values.name,
            slug: values.slug,
            priority: values.priority,
            dailyTarget: values.dailyTarget,
          },
        });
      } else {
        await createMutation.mutateAsync({
          name: values.name,
          slug: values.slug,
          priority: values.priority,
          dailyTarget: values.dailyTarget,
        });
      }
      setDialogOpen(false);
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Couldn't save the category.",
      );
    }
  }

  function toggleStatus(category: Category) {
    const targetStatus = category.status === "INACTIVE" ? "ACTIVE" : "INACTIVE";
    setBusyId(category.categoryId);
    statusMutation
      .mutateAsync({ categoryId: category.categoryId, status: targetStatus })
      .finally(() => setBusyId(null));
  }

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Categories</h1>
          <p className="text-sm text-muted-foreground">
            Organize products into categories and route each one to the
            Pinterest accounts and boards that publish it.
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
          <Button type="button" onClick={openCreate}>
            <Plus data-icon="inline-start" className="size-4" />
            New Category
          </Button>
        </div>
      </header>

      {isLoading ? (
        <CategoriesSkeleton />
      ) : isError ? (
        <EmptyState
          icon={Tags}
          title="Couldn't load Categories"
          description={
            (error as Error | undefined)?.message ??
            "The categories API did not respond."
          }
          action={
            <Button type="button" variant="outline" onClick={refresh}>
              Try again
            </Button>
          }
        />
      ) : categories.length === 0 ? (
        <EmptyState
          icon={Tags}
          title="No categories yet"
          description="Create a category to start organizing your product pipeline by topic."
          action={
            <Button type="button" onClick={openCreate}>
              <Plus data-icon="inline-start" className="size-4" />
              New Category
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map((category) => (
            <CategoryCard
              key={category.categoryId}
              category={category}
              busy={busyId === category.categoryId}
              onEdit={() => openEdit(category)}
              onToggleStatus={() => {
                if (category.status === "ACTIVE") {
                  setArchiveTarget(category);
                } else {
                  setRestoreTarget(category);
                }
              }}
            />
          ))}
        </div>
      )}

      <CategoryFormDialog
        key={editing?.categoryId ?? "new"}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        category={editing}
        submitting={createMutation.isPending || updateMutation.isPending}
        error={formError}
        onSubmit={handleSubmit}
      />

      <CategoryStatusConfirm
        target={archiveTarget}
        onClose={() => setArchiveTarget(null)}
        onConfirm={() => {
          if (archiveTarget) toggleStatus(archiveTarget);
          setArchiveTarget(null);
        }}
        title="Archive category?"
        description={`"${archiveTarget?.categoryName}" will stop routing new publishing. Its routes stay on record and it can be reactivated anytime.`}
        confirmLabel="Archive"
        busy={busyId !== null}
      />

      <CategoryStatusConfirm
        target={restoreTarget}
        onClose={() => setRestoreTarget(null)}
        onConfirm={() => {
          if (restoreTarget) toggleStatus(restoreTarget);
          setRestoreTarget(null);
        }}
        title="Reactivate category?"
        description={`"${restoreTarget?.categoryName}" will be available for routing again.`}
        confirmLabel="Reactivate"
        busy={busyId !== null}
      />
    </div>
  );
}

function CategoryCard({
  category,
  busy,
  onEdit,
  onToggleStatus,
}: {
  category: Category;
  busy: boolean;
  onEdit: () => void;
  onToggleStatus: () => void;
}) {
  const archived = category.status === "INACTIVE";

  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-xl border bg-card p-5 transition-colors",
        archived && "opacity-70",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl border bg-muted/50 text-muted-foreground">
            <Tags className="size-5" />
          </div>
          <div className="space-y-0.5">
            <Link
              href={`/categories/${category.categoryId}`}
              className="text-sm font-semibold tracking-tight hover:underline"
            >
              {category.categoryName}
            </Link>
            <p className="text-xs text-muted-foreground">
              {category.categorySlug ?? "no slug"}
            </p>
          </div>
        </div>
        <CategoryStatusBadge status={category.status} />
      </div>

      <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Layers className="size-3.5" />
          Priority {category.priority}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <CalendarClock className="size-3.5" />
          {category.dailyTarget}/day
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Users className="size-3.5" />
          {category.mappedAccounts} account
          {category.mappedAccounts === 1 ? "" : "s"}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Package className="size-3.5" />
          {category.mappedBoards} board
          {category.mappedBoards === 1 ? "" : "s"}
        </span>
      </div>

      <div className="mt-auto flex items-center justify-between gap-2 border-t pt-4">
        <Link
          href={`/categories/${category.categoryId}`}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:underline"
        >
          Manage routing
          <ArrowRight className="size-3.5" />
        </Link>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onEdit}
            disabled={busy}
          >
            Edit
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onToggleStatus}
            disabled={busy}
            className="text-destructive hover:text-destructive"
          >
            {archived ? "Reactivate" : "Archive"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function CategoryStatusConfirm({
  target,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel,
  busy,
}: {
  target: Category | null;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel: string;
  busy: boolean;
}) {
  return (
    <div className={cn("fixed inset-0 z-50", target === null && "hidden")}>
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className="w-full max-w-sm rounded-xl border bg-card p-6 shadow-lg">
          <h2 className="text-base font-semibold tracking-tight">{title}</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {description}
          </p>
          <div className="mt-6 flex items-center justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="button"
              variant={confirmLabel === "Archive" ? "destructive" : "default"}
              onClick={onConfirm}
              disabled={busy}
            >
              {busy ? "Working…" : confirmLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
