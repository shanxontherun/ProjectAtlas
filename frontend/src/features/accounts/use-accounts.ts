"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAccounts } from "./accounts-api";

export const ACCOUNTS_QUERY_KEY = ["accounts"] as const;

export function useAccounts() {
  return useQuery({
    queryKey: ACCOUNTS_QUERY_KEY,
    queryFn: fetchAccounts,
  });
}
