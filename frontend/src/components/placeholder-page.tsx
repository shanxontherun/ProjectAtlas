import type { ReactNode } from "react";
import { getNavItem } from "@/lib/navigation";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";

type PlaceholderPageProps = {
  href: string;
  emptyTitle: string;
  emptyDescription: string;
  action?: ReactNode;
};

export function PlaceholderPage({
  href,
  emptyTitle,
  emptyDescription,
  action,
}: PlaceholderPageProps) {
  const item = getNavItem(href);

  return (
    <>
      <PageHeader title={item?.title ?? ""} description={item?.description ?? ""} />
      <EmptyState
        icon={item?.icon ?? (() => null)}
        title={emptyTitle}
        description={emptyDescription}
        action={action}
      />
    </>
  );
}
