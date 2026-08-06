"use client";

function getGreeting(hour: number) {
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function formatLongDate(date: Date) {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(date);
}

type WelcomeHeaderProps = {
  subtitle: string;
};

export function WelcomeHeader({ subtitle }: WelcomeHeaderProps) {
  const now = new Date();

  return (
    <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
          {formatLongDate(now)}
        </p>
        <h1 className="text-2xl font-semibold tracking-tight">
          {getGreeting(now.getHours())}
        </h1>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>
    </header>
  );
}
