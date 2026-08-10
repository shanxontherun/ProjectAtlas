export type ConnectionStatus =
  | "NOT_CONFIGURED"
  | "NOT_CONNECTED"
  | "CONNECTING"
  | "CONNECTED"
  | "ERROR"
  | "DISCONNECTED"
  | "CONFIGURED";

export type ProviderId = "PINTEREST" | "AMAZON_ASSOCIATES" | "AI";

export type AccountRow = {
  connectionId: number | null;
  provider: ProviderId;
  displayName: string;
  username: string | null;
  marketplace: string | null;
  connectionStatus: ConnectionStatus;
  connectedAt: string | null;
  isSeed: boolean;
};

export type AccountProviderGroup = {
  provider: ProviderId;
  label: string;
  accounts: AccountRow[];
};

const CONNECTION_STATUSES: ConnectionStatus[] = [
  "NOT_CONFIGURED",
  "NOT_CONNECTED",
  "CONNECTING",
  "CONNECTED",
  "ERROR",
  "DISCONNECTED",
  "CONFIGURED",
];

const PROVIDERS: ProviderId[] = ["PINTEREST", "AMAZON_ASSOCIATES", "AI"];

function isConnectionStatus(value: unknown): value is ConnectionStatus {
  return (
    typeof value === "string" &&
    CONNECTION_STATUSES.includes(value as ConnectionStatus)
  );
}

function isProvider(value: unknown): value is ProviderId {
  return typeof value === "string" && PROVIDERS.includes(value as ProviderId);
}

export function mapAccount(row: unknown): AccountRow {
  const source =
    typeof row === "object" && row !== null
      ? (row as Record<string, unknown>)
      : {};

  const status = isConnectionStatus(source.connection_status)
    ? source.connection_status
    : "NOT_CONNECTED";

  const provider = isProvider(source.provider) ? source.provider : "AI";

  return {
    connectionId:
      typeof source.connection_id === "number" ? source.connection_id : null,
    provider,
    displayName:
      typeof source.display_name === "string"
        ? source.display_name
        : provider,
    username:
      typeof source.username === "string" ? source.username : null,
    marketplace:
      typeof source.marketplace === "string" ? source.marketplace : null,
    connectionStatus: status,
    connectedAt:
      typeof source.connected_at === "string" ? source.connected_at : null,
    isSeed: source.is_seed === true || source.is_seed === 1,
  };
}

export function mapProviderGroup(group: unknown): AccountProviderGroup {
  const source =
    typeof group === "object" && group !== null
      ? (group as Record<string, unknown>)
      : {};

  const provider = isProvider(source.provider) ? source.provider : "AI";
  const rawAccounts = Array.isArray(source.accounts) ? source.accounts : [];

  return {
    provider,
    label: typeof source.label === "string" ? source.label : provider,
    accounts: rawAccounts.map(mapAccount),
  };
}

export async function fetchAccounts(): Promise<AccountProviderGroup[]> {
  const response = await fetch("/api/accounts");
  if (!response.ok) {
    throw new Error(`Failed to load accounts (${response.status})`);
  }
  const payload: unknown = await response.json();
  if (!Array.isArray(payload)) {
    throw new Error("Unexpected accounts response");
  }
  return payload.map(mapProviderGroup);
}
