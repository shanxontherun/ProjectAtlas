import { Check, Lightbulb, Star } from "lucide-react";
import { cn } from "@/lib/utils";

const SCORE = 92;
const STRENGTHS = ["High contrast", "CTA visibility", "Pinterest friendly"];
const SUGGESTIONS = ["Shorten headline slightly", "Increase CTA emphasis"];

export function CreativeScore() {
  const filledStars = Math.round(SCORE / 20);

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <header className="space-y-0.5">
        <h2 className="text-sm font-semibold tracking-tight">Creative Score</h2>
        <p className="text-xs text-muted-foreground">
          Quality estimate from the creative engine.
        </p>
      </header>

      <div className="flex items-end gap-1.5">
        <span className="text-4xl leading-none font-semibold tracking-tight tabular-nums">
          {SCORE}
        </span>
        <span className="pb-0.5 text-sm text-muted-foreground">/ 100</span>
      </div>

      <div
        role="img"
        aria-label={`Rated ${SCORE} out of 100`}
        className="flex items-center gap-0.5"
      >
        {Array.from({ length: 5 }).map((_, index) => (
          <Star
            key={index}
            aria-hidden="true"
            className={cn(
              "size-4",
              index < filledStars
                ? "fill-amber-500/90 text-amber-500/90 dark:fill-amber-400/90 dark:text-amber-400/90"
                : "text-muted-foreground/40",
            )}
          />
        ))}
      </div>

      <div className="flex flex-col gap-4">
        <div className="space-y-1.5">
          <h3 className="text-xs font-medium text-muted-foreground">
            Strengths
          </h3>
          <ul className="flex flex-col gap-1">
            {STRENGTHS.map((strength) => (
              <li key={strength} className="flex items-center gap-1.5 text-xs">
                <Check
                  className="size-3.5 shrink-0 text-emerald-600 dark:text-emerald-400"
                  aria-hidden="true"
                />
                <span className="font-medium text-foreground">{strength}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-1.5">
          <h3 className="text-xs font-medium text-muted-foreground">
            Suggestions
          </h3>
          <ul className="flex flex-col gap-1">
            {SUGGESTIONS.map((suggestion) => (
              <li key={suggestion} className="flex items-center gap-1.5 text-xs">
                <Lightbulb
                  className="size-3.5 shrink-0 text-amber-600 dark:text-amber-400"
                  aria-hidden="true"
                />
                <span className="text-muted-foreground">{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
