"use client";

import { useMemo, useState } from "react";
import { ArrowRight, Pin, Plus, RefreshCw, Route } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useAddCategoryRoute,
  useBoards,
  useCategoryRoutes,
  useUpdateCategoryRoute,
} from "./use-categories";
import type { CategoryRoute } from "./types";

const fieldLabel = "text-xs font-medium text-muted-foreground";

export function CategoryRoutesCard({
  categoryId,
}: {
  categoryId: number;
}) {
  const queryClient = useQueryClient();
  const {
    data: routes = [],
    isLoading,
    isError,
  } = useCategoryRoutes(categoryId);
  const { data: boards = [], isLoading: boardsLoading } = useBoards();

  const [accountId, setAccountId] = useState<string>("");
  const [boardId, setBoardId] = useState<string>("");
  const [priority, setPriority] = useState("1");
  const [formError, setFormError] = useState<string | null>(null);

  const addMutation = useAddCategoryRoute(categoryId);
  const routeMutation = useUpdateCategoryRoute(categoryId);

  const accounts = useMemo(() => {
    const byId = new Map<
      number,
      { accountId: number; accountName: string; username: string | null }
    >();
    for (const board of boards) {
      if (!byId.has(board.accountId)) {
        byId.set(board.accountId, {
          accountId: board.accountId,
          accountName: board.accountName,
          username: board.username,
        });
      }
    }
    return [...byId.values()].sort((a, b) =>
      a.accountName.localeCompare(b.accountName),
    );
  }, [boards]);

  const boardsForAccount = useMemo(
    () =>
      boards
        .filter((board) => board.accountId === Number(accountId))
        .sort((a, b) => a.boardName.localeCompare(b.boardName)),
    [boards, accountId],
  );

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["categories"] });
  }

  function selectAccount(value: string) {
    setAccountId(value);
    setBoardId("");
  }

  async function handleAddRoute(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    if (!accountId || !boardId) {
      setFormError("Pick an account and a board for this route.");
      return;
    }

    try {
      await addMutation.mutateAsync({
        accountId: Number(accountId),
        boardId: Number(boardId),
        priority: Math.max(1, Number(priority) || 1),
      });
      setPriority("1");
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Couldn't add this route.",
      );
    }
  }

  async function toggleRoute(route: CategoryRoute) {
    await routeMutation.mutateAsync({
      routeId: route.routeId,
      patch: {
        status: route.routeStatus === "INACTIVE" ? "ACTIVE" : "INACTIVE",
      },
    });
  }

  return (
    <section className="flex flex-col gap-4 rounded-xl border bg-card p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-0.5">
          <h2 className="text-base font-semibold tracking-tight">
            Account &amp; board routing
          </h2>
          <p className="text-sm text-muted-foreground">
            Choose which Pinterest account and board publish this category.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={refresh}
          disabled={isLoading}
        >
          <RefreshCw data-icon="inline-start" className="size-4" />
          Refresh
        </Button>
      </div>

      {/* Add-route form */}
      <form
        onSubmit={handleAddRoute}
        className="grid grid-cols-1 gap-4 rounded-lg border border-dashed bg-muted/30 p-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_110px_auto]"
      >
        <div className="flex flex-col gap-1.5">
          <label className={fieldLabel} htmlFor="route-account">
            Pinterest account
          </label>
          {boardsLoading ? (
            <Skeleton className="h-8 w-full" />
          ) : accounts.length === 0 ? (
            <Select value={accountId} onValueChange={selectAccount}>
              <SelectTrigger id="route-account" className="w-full">
                <SelectValue placeholder="No accounts yet" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none" disabled>
                  Connect an account first
                </SelectItem>
              </SelectContent>
            </Select>
          ) : (
            <Select value={accountId} onValueChange={selectAccount}>
              <SelectTrigger id="route-account" className="w-full">
                <SelectValue placeholder="Select account" />
              </SelectTrigger>
              <SelectContent align="start">
                {accounts.map((account) => (
                  <SelectItem
                    key={account.accountId}
                    value={String(account.accountId)}
                  >
                    {account.accountName}
                    {account.username ? ` (${account.username})` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className={fieldLabel} htmlFor="route-board">
            Pinterest board
          </label>
          <Select
            value={boardId}
            onValueChange={setBoardId}
            disabled={!accountId || boardsForAccount.length === 0}
          >
            <SelectTrigger id="route-board" className="w-full">
              <SelectValue
                placeholder={
                  accountId ? "Select board" : "Pick an account first"
                }
              />
            </SelectTrigger>
            <SelectContent align="start">
              {boardsForAccount.length === 0 ? (
                <SelectItem value="__none" disabled>
                  No boards for this account
                </SelectItem>
              ) : (
                boardsForAccount.map((board) => (
                  <SelectItem
                    key={board.boardId}
                    value={String(board.boardId)}
                  >
                    {board.boardName}
                    {board.pinterestBoardId
                      ? ` · ${board.pinterestBoardId}`
                      : ""}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className={fieldLabel} htmlFor="route-priority">
            Priority
          </label>
          <Input
            id="route-priority"
            type="number"
            min={1}
            value={priority}
            onChange={(event) => setPriority(event.target.value)}
          />
        </div>

        <div className="flex items-end">
          <Button
            type="submit"
            disabled={addMutation.isPending || !accountId || !boardId}
            className="w-full sm:w-auto"
          >
            <Plus data-icon="inline-start" className="size-4" />
            Add Route
          </Button>
        </div>
      </form>

      {formError && (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {formError}
        </p>
      )}

      {!boardsLoading && boards.length === 0 && (
        <p className="rounded-lg border border-dashed px-3 py-3 text-sm text-muted-foreground">
          No Pinterest boards are available yet. Connect a Pinterest account
          to start routing categories.
        </p>
      )}

      {/* Routes list */}
      {isLoading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-14 w-full" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState
          icon={Route}
          title="Couldn't load routes"
          description="The routes API did not respond."
          action={
            <Button type="button" variant="outline" onClick={refresh}>
              Try again
            </Button>
          }
        />
      ) : routes.length === 0 ? (
        <EmptyState
          icon={Route}
          title="No routes yet"
          description="Add a route above to send this category to a Pinterest account and board."
          className="py-10"
        />
      ) : (
        <div className="flex flex-col gap-2">
          {routes.map((route) => (
            <RouteRow
              key={route.routeId}
              route={route}
              busy={routeMutation.isPending}
              onToggle={() => toggleRoute(route)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function RouteRow({
  route,
  busy,
  onToggle,
}: {
  route: CategoryRoute;
  busy: boolean;
  onToggle: () => void;
}) {
  const archived = route.routeStatus === "INACTIVE";

  return (
    <div
      className={
        "flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-muted/20 px-4 py-3" +
        (archived ? " opacity-60" : "")
      }
    >
      <div className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1">
        <div className="min-w-0">
          <p className="text-sm font-medium tracking-tight">
            {route.accountName ?? `Account ${route.accountId}`}
          </p>
          <p className="text-xs text-muted-foreground">
            {route.username ?? "unknown username"}
            {route.isSeed ? " · sample account" : ""}
          </p>
        </div>
        <ArrowRight className="size-4 text-muted-foreground" />
        <div className="min-w-0">
          <p className="inline-flex items-center gap-1.5 text-sm font-medium tracking-tight">
            <Pin className="size-3.5 text-muted-foreground" />
            {route.boardName ?? `Board ${route.boardId}`}
          </p>
          {route.pinterestBoardId ? (
            <p className="text-xs text-muted-foreground">
              Pinterest board: {route.pinterestBoardId}
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">
              Board #{route.boardId}
            </p>
          )}
        </div>
        <Badge variant="secondary">Priority {route.priority}</Badge>
        {archived && <Badge variant="outline">Archived</Badge>}
      </div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={onToggle}
        disabled={busy}
        className={!archived ? "text-destructive hover:text-destructive" : ""}
      >
        {archived ? "Restore" : "Archive"}
      </Button>
    </div>
  );
}
