import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Analytics",
};

export default function AnalyticsPage() {
  return (
    <PlaceholderPage
      href="/analytics"
      emptyTitle="No analytics yet"
      emptyDescription="Performance, click, and revenue charts will appear here as soon as the pipeline starts generating data."
    />
  );
}
