"use client";

import { useState } from "react";
import { Menu } from "lucide-react";
import { AtlasLogo } from "@/components/layout/atlas-logo";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

export function MobileSidebar() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className="lg:hidden"
          aria-label="Open navigation"
        >
          <Menu />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72 bg-sidebar p-0">
        <SheetTitle className="sr-only">Atlas navigation</SheetTitle>
        <div className="flex h-14 items-center gap-2.5 border-b border-sidebar-border px-4">
          <span className="flex size-7 shrink-0 items-center justify-center rounded-lg border border-sidebar-border bg-sidebar-accent/40 text-sidebar-foreground">
            <AtlasLogo className="size-4 shrink-0" />
          </span>
          <span className="truncate text-[15px] font-semibold tracking-tight">
            Atlas
          </span>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          <SidebarNav onNavigate={() => setOpen(false)} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
