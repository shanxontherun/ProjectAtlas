"use client";

import { Bell, CheckCircle2, Package, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const notifications = [
  {
    id: "1",
    icon: Package,
    title: "New products discovered",
    description: "12 products added to Kitchen Storage.",
    time: "2m ago",
  },
  {
    id: "2",
    icon: CheckCircle2,
    title: "Creative generation completed",
    description: "home_01 template rendered for 8 products.",
    time: "1h ago",
  },
  {
    id: "3",
    icon: TriangleAlert,
    title: "Publish failed",
    description: "Board \"Home Essentials\" rejected a pin. Retrying.",
    time: "3h ago",
  },
] as const;

export function NotificationsDropdown() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Notifications"
          className="relative"
        >
          <Bell />
          <span
            className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-chart-1 ring-2 ring-background"
            aria-hidden="true"
          />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0">
        <DropdownMenuLabel className="flex items-center justify-between px-3 py-2.5">
          <span>Notifications</span>
          <span className="text-xs font-normal text-muted-foreground">
            Preview only
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <div className="flex flex-col py-1">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className="flex gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-muted/60"
            >
              <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border bg-muted/50 text-muted-foreground">
                <notification.icon className="size-4" />
              </span>
              <div className="min-w-0 space-y-0.5">
                <p className="text-sm font-medium leading-tight">
                  {notification.title}
                </p>
                <p className="text-xs leading-snug text-muted-foreground">
                  {notification.description}
                </p>
              </div>
              <span className="ml-auto shrink-0 text-[11px] tabular-nums text-muted-foreground">
                {notification.time}
              </span>
            </div>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
