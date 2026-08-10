"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ACCOUNTS_QUERY_KEY, useAccounts } from "./use-accounts";
import { AccountProviderSection } from "./accounts-provider-section";
import { AccountsSkeleton } from "./accounts-skeleton";

export function AccountsPage() {
  const { data, isLoading, isError, error } = useAccounts();
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);

  async function refresh() {
    setRefreshing(true);
    try {
      await queryClient.invalidateQueries({
        queryKey: ACCOUNTS_QUERY_KEY,
        refetchType: "active",
      });
    } finally {
      setRefreshing(false);
    }
  }

  if (isLoading) {
    return <AccountsSkeleton />;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed bg-card/50 px-6 py-16 text-center">
        <p className="text-sm font-semibold tracking-tight">
          Couldn&apos;t load Accounts
        </p>
        <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
          {(error as Error | undefined)?.message ??
            "The accounts API did not respond."}
        </p>
        <Button type="button" variant="outline" onClick={refresh}>
          Try again
        </Button>
      </div>
    );
  }

  const groups = data ?? [];

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Accounts</h1>
          <p className="text-sm text-muted-foreground">
            Manage your connected platform accounts and integrations.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={refresh}
          disabled={refreshing}
        >
          <RefreshCw
            data-icon="inline-start"
            className={cn("size-4", refreshing && "animate-spin")}
          />
          Refresh
        </Button>
      </header>

      {groups.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed bg-card/50 px-6 py-16 text-center">
          <p className="text-sm font-semibold tracking-tight">
            No integrations configured
          </p>
          <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
            Accounts will appear here as integrations are configured.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {groups.map((group) => (
            <AccountProviderSection key={group.provider} group={group} />
          ))}
        </div>
      )}
    </div>
  );
}
