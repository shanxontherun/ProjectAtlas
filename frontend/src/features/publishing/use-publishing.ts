"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchPublishing,
  publishNow,
  queueCreative,
  removeCreative,
  schedulePin,
  updatePinBoard,
} from "./publishing-api";
import { CREATIVES_QUERY_KEY } from "@/features/creatives/use-creatives";

export const PUBLISHING_QUERY_KEY = ["publishing"] as const;

export function usePublishing() {
  return useQuery({
    queryKey: PUBLISHING_QUERY_KEY,
    queryFn: fetchPublishing,
  });
}

export function useQueueCreative() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (researchProductId: number) =>
      queueCreative(researchProductId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PUBLISHING_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: CREATIVES_QUERY_KEY });
    },
  });
}

export function useRemoveCreative() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (researchProductId: number) =>
      removeCreative(researchProductId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PUBLISHING_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: CREATIVES_QUERY_KEY });
    },
  });
}

export function useSchedulePin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      pinId,
      scheduledAt,
    }: {
      pinId: number;
      scheduledAt: string;
    }) => schedulePin(pinId, scheduledAt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PUBLISHING_QUERY_KEY });
    },
  });
}

export function usePublishNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pinId: number) => publishNow(pinId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PUBLISHING_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: CREATIVES_QUERY_KEY });
    },
  });
}

export function useUpdatePinBoard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      pinId,
      accountId,
      boardId,
    }: {
      pinId: number;
      accountId: number;
      boardId: number;
    }) => updatePinBoard(pinId, accountId, boardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PUBLISHING_QUERY_KEY });
    },
  });
}
