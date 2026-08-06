import type { Metadata } from "next";
import { ContentView } from "@/features/content/content-view";

export const metadata: Metadata = {
  title: "AI Studio",
};

export default function ContentPage() {
  return <ContentView />;
}
