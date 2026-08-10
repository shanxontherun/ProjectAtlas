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
  profileUrl: string | null;
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
    profileUrl:
      typeof source.profile_url === "string" && source.profile_url
        ? source.profile_url
        : null,
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

export type PinterestConnectErrorKind = "config" | "network" | "unknown";

export class PinterestConnectError extends Error {
  kind: PinterestConnectErrorKind;

  constructor(kind: PinterestConnectErrorKind, message: string) {
    super(message);
    this.name = "PinterestConnectError";
    this.kind = kind;
  }
}

export async function startPinterestConnect(): Promise<string> {
  const response = await fetch("/api/accounts/pinterest/connect");

  if (response.status === 503) {
    throw new PinterestConnectError(
      "config",
      "Pinterest isn't configured on the server. Add PINTEREST_CLIENT_ID, " +
        "PINTEREST_CLIENT_SECRET, and PINTEREST_REDIRECT_URI to enable it.",
    );
  }

  if (!response.ok) {
    throw new PinterestConnectError(
      "unknown",
      `Failed to start Pinterest OAuth (${response.status})`,
    );
  }

  const payload: unknown = await response.json();
  const authorizationUrl =
    typeof payload === "object" &&
    payload !== null &&
    typeof (payload as Record<string, unknown>).authorization_url === "string"
      ? ((payload as Record<string, unknown>).authorization_url as string)
      : null;

  if (!authorizationUrl) {
    throw new PinterestConnectError(
      "unknown",
      "Pinterest OAuth returned an invalid response.",
    );
  }

  return authorizationUrl;
}

export async function disconnectPinterestConnection(
  connectionId: number,
): Promise<void> {
  const response = await fetch("/api/accounts/pinterest/disconnect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ connection_id: connectionId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to disconnect Pinterest (${response.status})`);
  }
}
