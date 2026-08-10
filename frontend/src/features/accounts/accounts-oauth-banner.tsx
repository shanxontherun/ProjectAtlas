"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

type BannerKind = "success" | "partial" | "denied" | "error";

type BannerCopy = {
  title: string;
  description: string;
};

const BANNER_COPY: Record<BannerKind, BannerCopy> = {
  success: {
    title: "Pinterest connected",
    description:
      "Your Pinterest account is now connected. Boards have been synced to Atlas.",
  },
  partial: {
    title: "Pinterest connected",
    description:
      "Your Pinterest account was connected, but some boards could not be synced. Try reconnecting to refresh them.",
  },
  denied: {
    title: "Connection cancelled",
    description: "Pinterest sign-in was cancelled. No changes were made.",
  },
  error: {
    title: "Couldn't connect Pinterest",
    description:
      "Something went wrong while connecting your Pinterest account. Please try again.",
  },
};

function kindClass(kind: BannerKind) {
  switch (kind) {
    case "success":
      return "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
    case "partial":
      return "border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300";
    case "denied":
      return "border-border bg-muted/60 text-muted-foreground";
    case "error":
      return "border-red-500/25 bg-red-500/10 text-red-700 dark:text-red-300";
  }
}

function errorCopy(reason: string | null): BannerCopy {
  if (reason === "config") {
    return {
      title: "Pinterest isn't configured",
      description:
        "The server needs PINTEREST_CLIENT_ID, PINTEREST_CLIENT_SECRET and PINTEREST_REDIRECT_URI before accounts can be connected.",
    };
  }
  return BANNER_COPY.error;
}

function OAuthBannerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [visible, setVisible] = useState(true);
  const [status] = useState<string | null>(() =>
    searchParams.get("pinterest"),
  );
  const [reason] = useState<string | null>(() => searchParams.get("reason"));

  useEffect(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.has("pinterest")) {
      url.searchParams.delete("pinterest");
      url.searchParams.delete("reason");
      router.replace(url.pathname + url.search, { scroll: false });
    }
  }, [router]);

  if (!visible || !status) {
    return null;
  }

  let kind: BannerKind;
  let copy: BannerCopy;

  if (status === "success") {
    kind = "success";
    copy = BANNER_COPY.success;
  } else if (status === "partial") {
    kind = "partial";
    copy = BANNER_COPY.partial;
  } else if (status === "denied") {
    kind = "denied";
    copy = BANNER_COPY.denied;
  } else {
    kind = "error";
    copy = errorCopy(reason);
  }

  return (
    <div
      role="status"
      className={cn(
        "flex items-start justify-between gap-4 rounded-xl border px-4 py-3",
        kindClass(kind),
      )}
    >
      <div className="min-w-0">
        <p className="text-sm font-semibold tracking-tight">{copy.title}</p>
        <p className="mt-0.5 text-sm leading-relaxed opacity-90">
          {copy.description}
        </p>
      </div>
      <button
        type="button"
        onClick={() => setVisible(false)}
        aria-label="Dismiss"
        className="shrink-0 rounded-md p-1 opacity-70 transition-opacity hover:opacity-100"
      >
        <X data-icon="inline-start" className="size-4" />
      </button>
    </div>
  );
}

export function AccountsOAuthBanner() {
  return <OAuthBannerContent />;
}
