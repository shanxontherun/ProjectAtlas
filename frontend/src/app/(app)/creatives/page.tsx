import type { Metadata } from "next";
import { Plus } from "lucide-react";
import { PlaceholderPage } from "@/components/placeholder-page";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Creatives",
};

export default function CreativesPage() {
  return (
    <PlaceholderPage
      href="/creatives"
      emptyTitle="No creatives yet"
      emptyDescription="Rendered creative assets generated from your content will appear here, ready for your platforms."
      action={
        <Button disabled>
          <Plus />
          Create creative
        </Button>
      }
    />
  );
}
