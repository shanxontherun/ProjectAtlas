import Link from "next/link";
import {
  ImageIcon,
  PackagePlus,
  Send,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { SectionCard } from "./section-card";
import type { QuickAction } from "./types";

const ACTION_ICONS: Record<string, LucideIcon> = {
  add_product: PackagePlus,
  generate_content: Sparkles,
  generate_creatives: ImageIcon,
  open_publishing: Send,
};

type QuickActionsProps = {
  actions: QuickAction[];
};

export function QuickActions({ actions }: QuickActionsProps) {
  return (
    <SectionCard title="Quick Actions">
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {actions.map((action) => {
          const Icon = ACTION_ICONS[action.id] ?? Sparkles;

          return (
            <li key={action.id}>
              <Link
                href={action.href}
                className="group flex h-full flex-col gap-3 rounded-xl border border-border bg-background p-4 outline-none transition-all duration-200 hover:-translate-y-0.5 hover:bg-muted/40 hover:shadow-lg hover:shadow-black/[0.04] focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="flex size-9 items-center justify-center rounded-lg border bg-muted/50 text-muted-foreground transition-colors group-hover:text-foreground">
                    <Icon className="size-4" aria-hidden="true" />
                  </span>
                  {action.count !== undefined && (
                    <span className="rounded-full border border-border bg-muted/40 px-2 py-0.5 text-xs font-semibold tabular-nums text-foreground">
                      {action.count}
                    </span>
                  )}
                </div>
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">{action.title}</p>
                  <p className="text-xs leading-snug text-muted-foreground">
                    {action.description}
                  </p>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </SectionCard>
  );
}
