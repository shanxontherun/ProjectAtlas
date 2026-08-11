"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  addCategoryRoute,
  createCategory,
  fetchBoards,
  fetchCategories,
  fetchCategory,
  fetchCategoryRoutes,
  setCategoryStatus,
  updateCategory,
  updateCategoryRoute,
} from "./categories-api";
import type {
  CategoryInput,
  CategoryRouteInput,
  CategoryStatus,
} from "./types";

export const CATEGORIES_QUERY_KEY = ["categories"] as const;
export const BOARDS_QUERY_KEY = ["boards"] as const;

function routesKey(categoryId: number) {
  return [...CATEGORIES_QUERY_KEY, categoryId, "routes"] as const;
}

export function useCategories() {
  return useQuery({
    queryKey: CATEGORIES_QUERY_KEY,
    queryFn: fetchCategories,
  });
}

export function useCategory(categoryId: number) {
  return useQuery({
    queryKey: [...CATEGORIES_QUERY_KEY, categoryId] as const,
    queryFn: () => fetchCategory(categoryId),
    enabled: categoryId > 0,
  });
}

export function useCategoryRoutes(categoryId: number) {
  return useQuery({
    queryKey: routesKey(categoryId),
    queryFn: () => fetchCategoryRoutes(categoryId),
    enabled: categoryId > 0,
  });
}

export function useBoards() {
  return useQuery({
    queryKey: BOARDS_QUERY_KEY,
    queryFn: fetchBoards,
  });
}

function invalidateCategories(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({
    queryKey: CATEGORIES_QUERY_KEY,
    refetchType: "active",
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CategoryInput) => createCategory(input),
    onSuccess: () => invalidateCategories(queryClient),
  });
}

export function useUpdateCategory(categoryId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Partial<CategoryInput>) =>
      updateCategory(categoryId, input),
    onSuccess: () => {
      invalidateCategories(queryClient);
      queryClient.invalidateQueries({
        queryKey: [...CATEGORIES_QUERY_KEY, categoryId],
        refetchType: "active",
      });
    },
  });
}

export function useSetCategoryStatus(categoryId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (status: CategoryStatus) =>
      setCategoryStatus(categoryId, status),
    onSuccess: () => {
      invalidateCategories(queryClient);
      queryClient.invalidateQueries({
        queryKey: [...CATEGORIES_QUERY_KEY, categoryId],
        refetchType: "active",
      });
    },
  });
}

export function useAddCategoryRoute(categoryId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CategoryRouteInput) =>
      addCategoryRoute(categoryId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: routesKey(categoryId),
        refetchType: "active",
      });
      invalidateCategories(queryClient);
    },
  });
}

export function useUpdateCategoryRoute(categoryId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (args: {
      routeId: number;
      patch: { priority?: number; status?: CategoryStatus };
    }) => updateCategoryRoute(categoryId, args.routeId, args.patch),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: routesKey(categoryId),
        refetchType: "active",
      });
      invalidateCategories(queryClient);
    },
  });
}
