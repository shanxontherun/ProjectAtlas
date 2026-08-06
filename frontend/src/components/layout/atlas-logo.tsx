import { useId } from "react";
import { cn } from "@/lib/utils";

export function AtlasLogo({ className }: { className?: string }) {
  const gradientId = useId();

  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className={cn("size-6", className)}
    >
      <defs>
        <linearGradient id={gradientId} x1="8" y1="8" x2="17" y2="17">
          <stop offset="0%" stopColor="var(--sidebar-primary)" />
          <stop offset="100%" stopColor="var(--chart-1)" />
        </linearGradient>
      </defs>
      <circle cx="12" cy="12" r="4.5" fill={`url(#${gradientId})`} />
      <ellipse
        cx="12"
        cy="12"
        rx="9.5"
        ry="3.9"
        stroke="currentColor"
        strokeWidth="1.6"
        transform="rotate(-24 12 12)"
      />
    </svg>
  );
}
