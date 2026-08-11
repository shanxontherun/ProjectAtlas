import type {
  Board,
  Category,
  CategoryInput,
  CategoryRoute,
  CategoryRouteInput,
  CategoryStatus,
} from "./types";

function isCategoryStatus(value: unknown): value is CategoryStatus {
  return value === "ACTIVE" || value === "INACTIVE";
}

function asString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function asNumber(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function asBoolean(value: unknown): boolean {
  return value === true || value === 1;
}

function mapCategory(row: Record<string, unknown>): Category {
  return {
    categoryId: asNumber(row.category_id),
    categoryName: asString(row.category_name) ?? "",
    categorySlug: asString(row.category_slug),
    priority: asNumber(row.priority),
    status: isCategoryStatus(row.status) ? row.status : "ACTIVE",
    dailyTarget: asNumber(row.daily_target),
    createdAt: asString(row.created_at) ?? "",
    updatedAt: asString(row.updated_at) ?? "",
    activeRoutes: asNumber(row.active_routes),
    mappedAccounts: asNumber(row.mapped_accounts),
    mappedBoards: asNumber(row.mapped_boards),
  };
}

function mapCategoryRoute(row: Record<string, unknown>): CategoryRoute {
  return {
    routeId: asNumber(row.route_id),
    categoryId: asNumber(row.category_id),
    categorySlug: asString(row.category_slug),
    accountId: asNumber(row.account_id),
    accountName: asString(row.account_name),
    username: asString(row.username),
    isSeed: asBoolean(row.is_seed),
    connectionStatus: asString(row.connection_status),
    boardId: asNumber(row.board_id),
    boardName: asString(row.board_name),
    pinterestBoardId: asString(row.pinterest_board_id),
    privacy: asString(row.privacy),
    boardStatus: asString(row.board_status),
    priority: asNumber(row.priority),
    routeStatus: isCategoryStatus(row.route_status)
      ? row.route_status
      : "ACTIVE",
    routeCreatedAt: asString(row.route_created_at) ?? "",
  };
}

function mapBoard(row: Record<string, unknown>): Board {
  return {
    boardId: asNumber(row.board_id),
    accountId: asNumber(row.account_id),
    boardName: asString(row.board_name) ?? "",
    pinterestBoardId: asString(row.pinterest_board_id),
    privacy: asString(row.privacy),
    status: asString(row.status) ?? "ACTIVE",
    accountName: asString(row.account_name) ?? "",
    username: asString(row.username),
    isSeed: asBoolean(row.is_seed),
  };
}

async function readRows(response: Response): Promise<Record<string, unknown>[]> {
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  const payload: unknown = await response.json();
  if (!Array.isArray(payload)) {
    throw new Error("Unexpected response shape");
  }
  return payload as Record<string, unknown>[];
}

async function readRow(response: Response): Promise<Record<string, unknown>> {
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  const payload: unknown = await response.json();
  if (typeof payload !== "object" || payload === null) {
    throw new Error("Unexpected response shape");
  }
  return payload as Record<string, unknown>;
}

export async function fetchCategories(): Promise<Category[]> {
  const response = await fetch("/api/categories");
  const rows = await readRows(response);
  return rows.map(mapCategory);
}

export async function fetchCategory(categoryId: number): Promise<Category> {
  const response = await fetch(`/api/categories/${categoryId}`);
  return mapCategory(await readRow(response));
}

export async function createCategory(
  input: CategoryInput,
): Promise<Category> {
  const response = await fetch("/api/categories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: input.name,
      slug: input.slug ?? null,
      priority: input.priority,
      daily_target: input.dailyTarget,
      status: input.status ?? "ACTIVE",
    }),
  });
  return mapCategory(await readRow(response));
}

export async function updateCategory(
  categoryId: number,
  input: Partial<CategoryInput>,
): Promise<Category> {
  const response = await fetch(`/api/categories/${categoryId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: input.name,
      slug: input.slug,
      priority: input.priority,
      daily_target: input.dailyTarget,
      status: input.status,
    }),
  });
  return mapCategory(await readRow(response));
}

export async function setCategoryStatus(
  categoryId: number,
  status: CategoryStatus,
): Promise<Category> {
  const action = status === "INACTIVE" ? "archive" : "activate";
  const response = await fetch(`/api/categories/${categoryId}/${action}`, {
    method: "POST",
  });
  return mapCategory(await readRow(response));
}

export async function fetchCategoryRoutes(
  categoryId: number,
): Promise<CategoryRoute[]> {
  const response = await fetch(`/api/categories/${categoryId}/routes`);
  const rows = await readRows(response);
  return rows.map(mapCategoryRoute);
}

export async function addCategoryRoute(
  categoryId: number,
  input: CategoryRouteInput,
): Promise<CategoryRoute> {
  const response = await fetch(`/api/categories/${categoryId}/routes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      account_id: input.accountId,
      board_id: input.boardId,
      priority: input.priority,
    }),
  });
  return mapCategoryRoute(await readRow(response));
}

export async function updateCategoryRoute(
  categoryId: number,
  routeId: number,
  patch: { priority?: number; status?: CategoryStatus },
): Promise<CategoryRoute> {
  const response = await fetch(
    `/api/categories/${categoryId}/routes/${routeId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    },
  );
  return mapCategoryRoute(await readRow(response));
}

export async function fetchBoards(): Promise<Board[]> {
  const response = await fetch("/api/boards");
  const rows = await readRows(response);
  return rows.map(mapBoard);
}
