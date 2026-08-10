"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/features/dashboard/section-card";
import {
  PinterestConnectError,
  startPinterestConnect,
  disconnectPinterestConnection,
  type AccountProviderGroup,
  type ConnectionStatus,
  type ProviderId,
} from "./accounts-api";
import { ACCOUNTS_QUERY_KEY } from "./use-accounts";
import { AccountRowView, sectionStatus } from "./accounts-account-row";
import { AccountStatusBadge } from "./accounts-status-badge";

type ProviderCopy = {
  description: string;
  ctaLabel?: string;
  emptyTitle: string;
  emptyDescription: string;
  seedNote?: string;
};

const PROVIDER_COPY: Record<ProviderId, ProviderCopy> = {
  PINTEREST: {
    description: "Connect Pinterest to publish Pins from Atlas.",
    ctaLabel: "Connect Pinterest",
    emptyTitle: "No Pinterest accounts yet",
    emptyDescription:
      "Connect a Pinterest account to sync your boards into Atlas and make them available for publishing.",
    seedNote:
      "The accounts below are development sample data. None of them are connected to Pinterest.",
  },
  AMAZON_ASSOCIATES: {
    description:
      "Configure Amazon Associates for automatic affiliate links.",
    ctaLabel: "Configure Amazon Associates",
    emptyTitle: "Not configured",
    emptyDescription:
      "Add an Amazon Associates account to enable automatic affiliate links. Affiliate generation comes in a later sprint.",
  },
  AI: {
    description:
      "AI providers are configured through your environment settings. Keys stay server-side.",
    emptyTitle: "No AI providers",
    emptyDescription:
      "Configure AI_BASE_URL, AI_API_KEY and AI_MODEL to enable an AI provider.",
  },
};

const EMPTY_STATUS: ConnectionStatus = "NOT_CONFIGURED";

function statusBadge(status: ConnectionStatus | "EMPTY") {
  if (status === "EMPTY") {
    return <AccountStatusBadge status={EMPTY_STATUS} />;
  }
  return <AccountStatusBadge status={status} />;
}

function ActionButton({ label }: { label: string }) {
  return (
    <Button type="button" disabled title="Coming in a later sprint">
      {label}
    </Button>
  );
}

type PinterestConnectButtonProps = {
  variant?: "default" | "outline";
};

function PinterestConnectButton({
  variant = "default",
}: PinterestConnectButtonProps) {
  const queryClient = useQueryClient();
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConnect() {
    if (connecting) {
      return;
    }
    setConnecting(true);
    setError(null);
    try {
      const authorizationUrl = await startPinterestConnect();
      await queryClient.invalidateQueries({
        queryKey: ACCOUNTS_QUERY_KEY,
        refetchType: "none",
      });
      window.location.assign(authorizationUrl);
    } catch (err) {
      setConnecting(false);
      if (err instanceof PinterestConnectError) {
        setError(err.message);
      } else {
        setError("Couldn't reach the server. Please try again.");
      }
    }
  }

  return (
    <div className="flex flex-col items-end gap-2">
      <Button
        type="button"
        variant={variant}
        onClick={handleConnect}
        disabled={connecting}
      >
        {connecting ? "Opening Pinterest..." : "Connect Pinterest"}
      </Button>
      {error ? (
        <p
          role="alert"
          className="max-w-sm text-xs leading-relaxed text-red-600 dark:text-red-400"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}

type AccountProviderSectionProps = {
  group: AccountProviderGroup;
};

export function AccountProviderSection({
  group,
}: AccountProviderSectionProps) {
  const queryClient = useQueryClient();
  const [disconnectingId, setDisconnectingId] = useState<number | null>(null);

  const copy = PROVIDER_COPY[group.provider] ?? PROVIDER_COPY.AI;
  const status = sectionStatus(group.accounts);
  const hasAccounts = group.accounts.length > 0;
  const showSeedNote =
    group.provider === "PINTEREST" &&
    group.accounts.some((account) => account.isSeed);

  async function handleDisconnect(connectionId: number) {
    if (disconnectingId !== null) {
      return;
    }
    setDisconnectingId(connectionId);
    try {
      await disconnectPinterestConnection(connectionId);
    } finally {
      setDisconnectingId(null);
      await queryClient.invalidateQueries({ queryKey: ACCOUNTS_QUERY_KEY });
    }
  }

  const connectAction =
    group.provider === "PINTEREST" ? (
      <PinterestConnectButton />
    ) : copy.ctaLabel ? (
      <ActionButton label={copy.ctaLabel} />
    ) : undefined;

  const emptyState = (
    <EmptyState
      icon={ActionIcon}
      title={copy.emptyTitle}
      description={copy.emptyDescription}
      action={connectAction}
    />
  );

  return (
    <SectionCard
      title={group.label}
      description={copy.description}
      action={statusBadge(status)}
    >
      {hasAccounts ? (
        <div className="flex flex-col gap-4">
          <ul className="flex flex-col gap-3">
            {group.accounts.map((account) => (
              <AccountRowView
                key={
                  account.connectionId !== null
                    ? account.connectionId
                    : `${account.provider}-${account.displayName}`
                }
                account={account}
                disconnecting={
                  account.connectionId !== null &&
                  disconnectingId === account.connectionId
                }
                onDisconnect={
                  group.provider === "PINTEREST"
                    ? handleDisconnect
                    : undefined
                }
              />
            ))}
          </ul>
          {showSeedNote ? (
            <p className="text-xs text-muted-foreground">{copy.seedNote}</p>
          ) : null}
          {connectAction ? (
            <div className="flex justify-end">{connectAction}</div>
          ) : null}
        </div>
      ) : (
        emptyState
      )}
    </SectionCard>
  );
}

function ActionIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M12 17v5" />
      <path d="M9 10.76a2 2 0 0 1-1.11 1.79 2 2 0 0 0 1.11 3.45h6a2 2 0 0 0 1.11-3.45 2 2 0 0 1-1.11-1.79V9.5a3 3 0 1 0-6 0Z" />
    </svg>
  );
}
