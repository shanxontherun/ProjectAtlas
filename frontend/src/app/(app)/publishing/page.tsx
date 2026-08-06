import type { Metadata } from "next";
import { PublishingCenter } from "@/features/publishing/publishing-center";

export const metadata: Metadata = {
  title: "Publishing Center",
};

export default function PublishingPage() {
  return <PublishingCenter />;
}
