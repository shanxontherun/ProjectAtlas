import type { Publication, PublishItem } from "./types";

const PRIORITY_RANK: Record<PublishItem["priority"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export type PublishCounts = {
  ready: number;
  scheduled: number;
  published: number;
  failed: number;
};

export function getPublishCounts(
  queue: PublishItem[],
  publications: Publication[],
): PublishCounts {
  const counts: PublishCounts = {
    ready: 0,
    scheduled: 0,
    published: 0,
    failed: 0,
  };

  for (const item of queue) {
    if (item.status === "scheduled") counts.scheduled += 1;
    else counts.ready += 1;
  }

  for (const publication of publications) {
    if (publication.status === "published") counts.published += 1;
    else if (publication.status === "scheduled") counts.scheduled += 1;
    else counts.failed += 1;
  }

  return counts;
}

export function sortQueue(items: PublishItem[]) {
  return [...items].sort((a, b) => {
    if (a.status !== b.status) {
      return a.status === "queued" ? -1 : 1;
    }
    return PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority];
  });
}

export function sortPublications(items: Publication[]) {
  return [...items].sort((a, b) => {
    const aUpcoming = a.status === "scheduled";
    const bUpcoming = b.status === "scheduled";

    if (aUpcoming && !bUpcoming) return -1;
    if (!aUpcoming && bUpcoming) return 1;
    if (aUpcoming && bUpcoming) {
      return +new Date(a.eventAt) - +new Date(b.eventAt);
    }
    return +new Date(b.eventAt) - +new Date(a.eventAt);
  });
}

function startOfDay(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

export function formatPublishTime(iso: string, now = new Date()) {
  const date = new Date(iso);
  const time = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
  const day = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
  }).format(date);

  const diffDays = Math.round(
    (startOfDay(date) - startOfDay(now)) / 86_400_000,
  );

  if (diffDays === 0) return `Today at ${time}`;
  if (diffDays === 1) return `Tomorrow at ${time}`;
  if (diffDays === -1) return `Yesterday at ${time}`;
  return `${day} at ${time}`;
}

export function relativeTime(iso: string, now = new Date()) {
  const minutes = Math.round((now.getTime() - new Date(iso).getTime()) / 60_000);

  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

export function formatCount(value: number) {
  if (value >= 1000) {
    const scaled = value / 1000;
    const formatted =
      value >= 10_000
        ? Math.round(scaled)
        : Number(scaled.toFixed(1)).toString();
    return `${formatted}k`;
  }
  return String(value);
}

export function toDatetimeLocal(date: Date) {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate(),
  )}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function defaultScheduleTime(now = new Date()) {
  const rounded = new Date(now.getTime() + 2 * 3_600_000);
  rounded.setMinutes(Math.ceil(rounded.getMinutes() / 30) * 30, 0, 0);
  return rounded;
}
