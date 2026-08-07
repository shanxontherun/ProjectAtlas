"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  approveCreative,
  fetchCreatives,
  generateCreative,
  reopenCreative,
  saveCreative,
  type CreativePresentationPayload,
} from "./creative-api";

export const CREATIVES_QUERY_KEY = ["creatives"] as const;

export function useCreatives() {
  return useQuery({
    queryKey: CREATIVES_QUERY_KEY,
    queryFn: fetchCreatives,
  });
}

export function useGenerateCreative() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      researchProductId,
      presentation,
    }: {
      researchProductId: number;
      presentation?: CreativePresentationPayload;
    }) => generateCreative(researchProductId, presentation),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CREATIVES_QUERY_KEY });
    },
  });
}

export function useApproveCreative() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      researchProductId,
      presentation,
    }: {
      researchProductId: number;
      presentation?: CreativePresentationPayload;
    }) => approveCreative(researchProductId, presentation),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CREATIVES_QUERY_KEY });
    },
  });
}

export function useSaveCreative() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      researchProductId,
      presentation,
    }: {
      researchProductId: number;
      presentation: CreativePresentationPayload;
    }) => saveCreative(researchProductId, presentation),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CREATIVES_QUERY_KEY });
    },
  });
}

export function useReopenCreative() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (researchProductId: number) =>
      reopenCreative(researchProductId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CREATIVES_QUERY_KEY });
    },
  });
}
