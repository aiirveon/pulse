interface AlertBannerProps {
  pct:     number;
  message: string;
}

export function AlertBanner({ pct, message }: AlertBannerProps) {
  return (
    <div className="border border-alert-border bg-alert-bg px-4 py-3 flex items-start gap-3">
      <span className="w-2 h-2 rounded-full bg-alert-border shrink-0 mt-0.5 status-pulse" />
      <div className="space-y-0.5">
        <p className="text-[9px] tracking-widest uppercase text-alert-border">
          NEGATIVE SENTIMENT SPIKE
        </p>
        <p className="text-xs text-foreground leading-relaxed">{message}</p>
        <p className="text-[9px] text-muted-foreground font-mono">
          {pct.toFixed(1)}% of last 30 posts
        </p>
      </div>
    </div>
  );
}
