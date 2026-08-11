import type { Metadata } from "next";
import { CategoryDetailPage } from "@/features/categories/category-detail";

export const metadata: Metadata = {
  title: "Category",
};

export default function CategoryDetailRoute() {
  return <CategoryDetailPage />;
}
