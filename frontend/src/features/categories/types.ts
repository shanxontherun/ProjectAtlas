export type CategoryStatus = "ACTIVE" | "INACTIVE";

export type Category = {
  categoryId: number;
  categoryName: string;
  categorySlug: string | null;
  priority: number;
  status: CategoryStatus;
  dailyTarget: number;
  createdAt: string;
  updatedAt: string;
  activeRoutes: number;
  mappedAccounts: number;
  mappedBoards: number;
};

export type CategoryRoute = {
  routeId: number;
  categoryId: number;
  categorySlug: string | null;
  accountId: number;
  accountName: string | null;
  username: string | null;
  isSeed: boolean;
  connectionStatus: string | null;
  boardId: number;
  boardName: string | null;
  pinterestBoardId: string | null;
  privacy: string | null;
  boardStatus: string | null;
  priority: number;
  routeStatus: CategoryStatus;
  routeCreatedAt: string;
};

export type Board = {
  boardId: number;
  accountId: number;
  boardName: string;
  pinterestBoardId: string | null;
  privacy: string | null;
  status: string;
  accountName: string;
  username: string | null;
  isSeed: boolean;
};

export type CategoryInput = {
  name: string;
  slug?: string | null;
  priority: number;
  dailyTarget: number;
  status?: CategoryStatus;
};

export type CategoryRouteInput = {
  accountId: number;
  boardId: number;
  priority: number;
};
