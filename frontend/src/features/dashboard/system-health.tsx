import { CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { SectionCard } from "./section-card";
import type { SystemService } from "./types";

type SystemHealthProps = {
  services: SystemService[];
};

export function SystemHealth({ services }: SystemHealthProps) {
  return (
    <SectionCard title="System Health">
      <div className="flex items-center gap-2.5">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 className="size-4" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium">Everything looks healthy today.</p>
          <p className="text-xs text-muted-foreground">
            All services are online and your pipeline is running as expected.
          </p>
        </div>
      </div>

      <ul className="grid grid-cols-1 gap-x-4 gap-y-5 border-t border-border/60 pt-4 sm:grid-cols-2 lg:grid-cols-4">
        {services.map((service) => (
          <li key={service.id} className="flex items-center gap-2.5">
            <span
              className={cn(
                "size-2 shrink-0 rounded-full bg-emerald-500",
                "ring-2 ring-emerald-500/20",
              )}
              aria-hidden="true"
            />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{service.label}</p>
              <p className="text-xs text-muted-foreground">
                {service.statusLabel}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}
