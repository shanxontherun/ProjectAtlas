"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  approveAiContent,
  fetchAiContent,
  generateAiContent,
} from "./content-api";

export const CONTENT_QUERY_KEY = ["content"] as const;

export function useContent() {
  return useQuery({
    queryKey: CONTENT_QUERY_KEY,
    queryFn: fetchAiContent,
  });
}

export function useGenerateContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: generateAiContent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONTENT_QUERY_KEY });
    },
  });
}

export function useApproveContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: approveAiContent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONTENT_QUERY_KEY });
    },
  });
}
