import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";
import { SectionCard } from "@/features/dashboard/section-card";
import type {
  AccountProviderGroup,
  ConnectionStatus,
  ProviderId,
} from "./accounts-api";
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
      "Connect a Pinterest account to start publishing Pins from Atlas. OAuth comes in a later sprint.",
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

type AccountProviderSectionProps = {
  group: AccountProviderGroup;
};

export function AccountProviderSection({
  group,
}: AccountProviderSectionProps) {
  const copy = PROVIDER_COPY[group.provider] ?? PROVIDER_COPY.AI;
  const status = sectionStatus(group.accounts);
  const hasAccounts = group.accounts.length > 0;
  const showSeedNote =
    group.provider === "PINTEREST" &&
    group.accounts.some((account) => account.isSeed);

  const emptyState = (
    <EmptyState
      icon={ActionIcon}
      title={copy.emptyTitle}
      description={copy.emptyDescription}
      action={
        copy.ctaLabel ? <ActionButton label={copy.ctaLabel} /> : undefined
      }
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
              />
            ))}
          </ul>
          {showSeedNote ? (
            <p className="text-xs text-muted-foreground">{copy.seedNote}</p>
          ) : null}
          {copy.ctaLabel ? (
            <div className="flex justify-end">
              <ActionButton label={copy.ctaLabel} />
            </div>
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
