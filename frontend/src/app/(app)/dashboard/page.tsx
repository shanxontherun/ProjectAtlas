import type { Metadata } from "next";
import { DashboardPage } from "@/features/dashboard/dashboard-page";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default function DashboardRoute() {
  return <DashboardPage />;
}
