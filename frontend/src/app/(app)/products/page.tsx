import type { Metadata } from "next";
import { PageHeader } from "@/components/page-header";
import { ProductsView } from "@/features/products/products-view";

export const metadata: Metadata = {
  title: "Products",
};

export default function ProductsPage() {
  return (
    <>
      <PageHeader
        title="Products"
        description="Manage the products in your Pinterest catalog pipeline."
      />
      <ProductsView />
    </>
  );
}
