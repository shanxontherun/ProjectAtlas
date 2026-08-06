import type { Metadata } from "next";
import { Plus } from "lucide-react";
import { PlaceholderPage } from "@/components/placeholder-page";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Content",
};

export default function ContentPage() {
  return (
    <PlaceholderPage
      href="/content"
      emptyTitle="No content yet"
      emptyDescription="AI-generated titles, descriptions, and hashtags for approved products will appear here for review and approval."
      action={
        <Button disabled>
          <Plus />
          Generate content
        </Button>
      }
    />
  );
}
