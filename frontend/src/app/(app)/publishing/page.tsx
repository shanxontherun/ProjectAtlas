import type { Metadata } from "next";
import { Plus } from "lucide-react";
import { PlaceholderPage } from "@/components/placeholder-page";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Publishing",
};

export default function PublishingPage() {
  return (
    <PlaceholderPage
      href="/publishing"
      emptyTitle="Nothing to publish yet"
      emptyDescription="Scheduled and published pins across your boards will appear here once content moves through the pipeline."
      action={
        <Button disabled>
          <Plus />
          Create schedule
        </Button>
      }
    />
  );
}
