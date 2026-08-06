import { cn } from "@/lib/utils";

export function AtlasLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className={cn("size-6", className)}
    >
      <circle cx="12" cy="12" r="4.5" fill="currentColor" />
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
