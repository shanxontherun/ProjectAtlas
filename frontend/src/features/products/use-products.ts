"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchProducts } from "./product-api";

export function useProducts() {
  return useQuery({
    queryKey: ["products"],
    queryFn: fetchProducts,
  });
}
