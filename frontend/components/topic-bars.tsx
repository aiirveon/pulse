import { topicDisplayName } from "@/lib/design-tokens";

interface TopicBarsProps {
  topicCounts: Record<string, number>;
}

export function TopicBars({ topicCounts }: TopicBarsProps) {
  const entries = Object.entries(topicCounts).sort((a, b) => b[1] - a[1]);
  const max     = Math.max(...entries.map(([, v]) => v), 1);

  if (entries.every(([, v]) => v === 0)) {
    return (
      <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
        No data yet
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {entries.map(([topic, count]) => {
        const pct = (count / max) * 100;
        return (
          <div key={topic} className="space-y-0.5">
            <div className="flex items-center justify-between">
              <span className="text-[9px] tracking-wider text-muted-foreground uppercase">
                {topicDisplayName[topic] ?? topic.replace(/_/g, " ")}
              </span>
              <span className="font-mono text-[9px] text-muted-foreground tabular-nums">
                {count}
              </span>
            </div>
            <div className="w-full h-[2px] bg-border/30">
              <div
                className="h-[2px] bg-primary score-bar transition-all duration-500"
                style={{ "--score-bar-width": `${pct}%` } as React.CSSProperties}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
