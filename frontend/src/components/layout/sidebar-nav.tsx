"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { navGroups } from "@/lib/navigation";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type SidebarNavProps = {
  collapsed?: boolean;
  onNavigate?: () => void;
};

export function SidebarNav({ collapsed = false, onNavigate }: SidebarNavProps) {
  const pathname = usePathname();

  const renderLink = (href: string, title: string, Icon: typeof navGroups[number]["items"][number]["icon"], active: boolean) => {
    const link = (
      <Link
        key={href}
        href={href}
        onClick={onNavigate}
        aria-current={active ? "page" : undefined}
        className={cn(
          "relative flex items-center gap-3 rounded-lg text-sm transition-colors",
          collapsed ? "justify-center px-0 py-2" : "px-3 py-2",
          active
            ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
            : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
        )}
      >
        {active && !collapsed && (
          <span
            aria-hidden="true"
            className="absolute top-1/2 left-0 h-4 w-[3px] -translate-y-1/2 rounded-r-full bg-sidebar-primary"
          />
        )}
        {active && collapsed && (
          <span
            aria-hidden="true"
            className="absolute top-1/2 left-1 h-4 w-[3px] -translate-y-1/2 rounded-r-full bg-sidebar-primary"
          />
        )}
        <Icon className="size-4 shrink-0" />
        {!collapsed && <span className="truncate">{title}</span>}
      </Link>
    );

    if (!collapsed) {
      return link;
    }

    return (
      <Tooltip key={href}>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent side="right" className="ml-2">
          {title}
        </TooltipContent>
      </Tooltip>
    );
  };

  return (
    <nav className="flex flex-col gap-4 p-2">
      {navGroups.map((group) => (
        <div key={group.label} className="flex flex-col gap-1">
          {!collapsed && (
            <p className="px-3 pt-1 pb-0.5 text-[10px] font-semibold tracking-widest text-muted-foreground/60 uppercase">
              {group.label}
            </p>
          )}
          {group.items.map((item) =>
            renderLink(
              item.href,
              item.title,
              item.icon,
              pathname === item.href,
            ),
          )}
        </div>
      ))}
    </nav>
  );
}
