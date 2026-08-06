import type { Metadata } from "next";
import { Plus } from "lucide-react";
import { PlaceholderPage } from "@/components/placeholder-page";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Accounts",
};

export default function AccountsPage() {
  return (
    <PlaceholderPage
      href="/accounts"
      emptyTitle="No connected accounts yet"
      emptyDescription="Connect your Pinterest accounts and boards to start publishing. Additional platforms are on the roadmap."
      action={
        <Button disabled>
          <Plus />
          Connect account
        </Button>
      }
    />
  );
}
