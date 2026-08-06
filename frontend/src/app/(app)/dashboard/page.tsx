import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default function DashboardPage() {
  return (
    <PlaceholderPage
      href="/dashboard"
      emptyTitle="Welcome to your dashboard"
      emptyDescription="Once the pipeline starts producing data, you'll see key metrics, recent activity, and a snapshot of your business across every channel here."
    />
  );
}
