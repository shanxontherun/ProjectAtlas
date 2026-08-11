"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { Category } from "./types";

const fieldLabel = "text-xs font-medium text-muted-foreground";

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

export type CategoryFormValues = {
  name: string;
  slug: string;
  priority: number;
  dailyTarget: number;
};

type CategoryFormDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  category?: Category | null;
  submitting: boolean;
  error: string | null;
  onSubmit: (values: CategoryFormValues) => void;
};

export function CategoryFormDialog({
  open,
  onOpenChange,
  category,
  submitting,
  error,
  onSubmit,
}: CategoryFormDialogProps) {
  // State is initialized from the target category so the form reflects it
  // immediately. Parents pass a stable `key` (category id, or "new") so the
  // dialog remounts whenever the editing target changes; values persist
  // while the same target stays selected across open/close cycles.
  const [name, setName] = useState(category?.categoryName ?? "");
  const [slug, setSlug] = useState(category?.categorySlug ?? "");
  const [priority, setPriority] = useState(String(category?.priority ?? 5));
  const [dailyTarget, setDailyTarget] = useState(
    String(category?.dailyTarget ?? 5),
  );
  // Tracks whether the user manually edited the slug field. While untouched,
  // the slug follows the name so renaming a category keeps it in sync.
  const [slugTouched, setSlugTouched] = useState(false);

  function handleNameChange(value: string) {
    setName(value);
    if (!slugTouched) setSlug(slugify(value));
  }

  const isEditing = category !== null && category !== undefined;

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    onSubmit({
      name: name.trim(),
      slug: slug.trim(),
      priority: Math.max(1, Number(priority) || 5),
      dailyTarget: Math.max(0, Number(dailyTarget) || 0),
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit Category" : "New Category"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update the category details and routing behavior."
              : "Create a category to organize Pinterest routing for products."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="category-name" className={fieldLabel}>
              Name
            </label>
            <Input
              id="category-name"
              value={name}
              onChange={(event) => handleNameChange(event.target.value)}
              placeholder="e.g. Kitchen Storage"
              required
              autoFocus
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="category-slug" className={fieldLabel}>
              Slug{" "}
              <span className="text-muted-foreground">
                (derived from the name, edit to override)
              </span>
            </label>
            <Input
              id="category-slug"
              value={slug}
              onChange={(event) => {
                setSlugTouched(true);
                setSlug(event.target.value);
              }}
              placeholder="e.g. kitchen_storage"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="category-priority" className={fieldLabel}>
                Priority
              </label>
              <Input
                id="category-priority"
                type="number"
                min={1}
                value={priority}
                onChange={(event) => setPriority(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="category-daily-target" className={fieldLabel}>
                Daily target
              </label>
              <Input
                id="category-daily-target"
                type="number"
                min={0}
                value={dailyTarget}
                onChange={(event) => setDailyTarget(event.target.value)}
              />
            </div>
          </div>

          {error && (
            <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting
                ? "Saving…"
                : isEditing
                  ? "Save Changes"
                  : "Create Category"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
