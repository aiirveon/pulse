import { EmotionBadge } from "@/components/emotion-badge";
import { topicDisplayName } from "@/lib/design-tokens";

interface FeedPostProps {
  content:          string;
  emotion:          string;
  confidence:       number;
  confidence_type?: string;
  topics:           Array<{ topic: string; confidence: number }>;
  source:           string;
  shap_words:       string[];
  degraded?:        boolean;
  error?:           string | null;
}

export function FeedPost({
  content, emotion, confidence, confidence_type, topics, source, shap_words, degraded, error,
}: FeedPostProps) {
  if (degraded) {
    return (
      <div className="bg-panel border border-destructive/40 p-3 space-y-1 opacity-70">
        <p className="text-sm text-foreground leading-relaxed">{content}</p>
        <p className="text-[9px] tracking-widest uppercase text-destructive font-mono">
          CLASSIFICATION FAILED — excluded from stats
          {error ? ` · ${error}` : ""}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-panel border border-border p-3 space-y-2">
      <p className="text-sm text-foreground leading-relaxed">{content}</p>

      <div className="flex items-center gap-2 flex-wrap">
        <EmotionBadge emotion={emotion} confidence={confidence} />
        {confidence_type === "estimated" && (
          <span className="text-[9px] tracking-widest uppercase text-muted-foreground font-mono border border-border px-1.5 py-0.5">
            est.
          </span>
        )}
        {topics.slice(0, 2).map((t, i) => (
          <span
            key={i}
            className="text-[9px] tracking-widest uppercase px-2 py-0.5 border border-border text-muted-foreground"
          >
            {topicDisplayName[t.topic] ?? t.topic.replace(/_/g, " ")}
          </span>
        ))}
        {source === "manual" && (
          <span className="ml-auto text-[9px] tracking-widest uppercase text-primary">
            MANUAL
          </span>
        )}
      </div>

      {shap_words.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {shap_words.slice(0, 4).map((word, i) => (
            <span
              key={i}
              className="text-[9px] px-1 py-0.5 bg-primary/10 border border-primary/20 text-primary font-mono"
            >
              {word}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
