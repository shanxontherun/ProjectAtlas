import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Settings",
};

export default function SettingsPage() {
  return (
    <PlaceholderPage
      href="/settings"
      emptyTitle="Workspace settings coming soon"
      emptyDescription="Team management, workspace configuration, and preferences will live here."
    />
  );
}
