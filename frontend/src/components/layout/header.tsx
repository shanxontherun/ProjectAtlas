"use client";

import { SearchCommand } from "@/components/layout/search-command";
import { MobileSidebar } from "@/components/layout/mobile-sidebar";
import { NotificationsDropdown } from "@/components/layout/notifications-dropdown";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { UserMenu } from "@/components/layout/user-menu";

export function Header() {
  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur-md md:px-6">
      <MobileSidebar />
      <SearchCommand />
      <div className="ml-auto flex items-center gap-1">
        <NotificationsDropdown />
        <ThemeToggle />
        <div className="mx-1 hidden h-5 w-px bg-border sm:block" />
        <UserMenu />
      </div>
    </header>
  );
}
