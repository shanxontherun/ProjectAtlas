import type { Metadata } from "next";
import { CreativeStudio } from "@/features/creatives/creative-studio";

export const metadata: Metadata = {
  title: "Creative Studio",
};

export default function CreativesPage() {
  return <CreativeStudio />;
}
