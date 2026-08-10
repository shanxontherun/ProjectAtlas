import type { ComponentType } from "react";
import { Button } from "@/components/ui/button";
import type { AccountRow, ConnectionStatus, ProviderId } from "./accounts-api";
import { AccountStatusBadge } from "./accounts-status-badge";

const PROVIDER_ICONS: Record<ProviderId, ComponentType<{ className?: string }>> = {
  PINTEREST: PinIcon,
  AMAZON_ASSOCIATES: ShoppingBagIcon,
  AI: SparklesIcon,
};

function PinIcon({ className }: { className?: string }) {
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

function ShoppingBagIcon({ className }: { className?: string }) {
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
      <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
      <path d="M3 6h18" />
      <path d="M16 10a4 4 0 0 1-8 0" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
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
      <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
    </svg>
  );
}

export function sectionStatus(
  accounts: AccountRow[],
): ConnectionStatus | "EMPTY" {
  if (accounts.length === 0) return "EMPTY";

  const statuses = new Set(accounts.map((account) => account.connectionStatus));

  if (statuses.has("CONNECTED")) return "CONNECTED";
  if (statuses.has("ERROR")) return "ERROR";
  if (statuses.has("CONFIGURED")) return "CONFIGURED";
  if (statuses.has("CONNECTING")) return "CONNECTING";
  if (statuses.size === 1 && statuses.has("NOT_CONFIGURED")) {
    return "NOT_CONFIGURED";
  }
  return "NOT_CONNECTED";
}

type AccountRowProps = {
  account: AccountRow;
  disconnecting?: boolean;
  onDisconnect?: (connectionId: number) => void;
};

export function AccountRowView({
  account,
  disconnecting = false,
  onDisconnect,
}: AccountRowProps) {
  const Icon = PROVIDER_ICONS[account.provider] ?? SparklesIcon;

  const meta = [
    account.username,
    account.marketplace ? `${account.marketplace} marketplace` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const showDisconnect =
    !account.isSeed &&
    account.connectionId !== null &&
    typeof onDisconnect === "function";

  return (
    <li className="flex items-center justify-between gap-4 rounded-xl border border-border bg-background/60 p-4">
      <div className="flex min-w-0 items-center gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-xl border bg-muted/50 text-muted-foreground">
          <Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-medium">{account.displayName}</p>
            {account.isSeed && (
              <span className="inline-flex shrink-0 items-center rounded-full border border-amber-500/25 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
                Sample
              </span>
            )}
          </div>
          {meta ? (
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              {meta}
            </p>
          ) : null}
          {account.profileUrl ? (
            <a
              href={account.profileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-0.5 inline-block truncate text-xs text-primary underline-offset-4 hover:underline"
            >
              {account.profileUrl}
            </a>
          ) : null}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <AccountStatusBadge status={account.connectionStatus} />
        {showDisconnect ? (
          <Button
            type="button"
            variant="ghost"
            size="xs"
            disabled={disconnecting}
            onClick={() => {
              if (account.connectionId !== null) {
                onDisconnect(account.connectionId);
              }
            }}
          >
            {disconnecting ? "Disconnecting..." : "Disconnect"}
          </Button>
        ) : null}
      </div>
    </li>
  );
}
