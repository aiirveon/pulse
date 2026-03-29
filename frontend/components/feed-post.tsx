import { EmotionBadge } from "@/components/emotion-badge";
import { topicDisplayName } from "@/lib/design-tokens";

interface FeedPostProps {
  content:    string;
  emotion:    string;
  confidence: number;
  topics:     Array<{ topic: string; confidence: number }>;
  source:     string;
  shap_words: string[];
}

export function FeedPost({
  content, emotion, confidence, topics, source, shap_words,
}: FeedPostProps) {
  return (
    <div className="bg-panel border border-border p-3 space-y-2">
      <p className="text-sm text-foreground leading-relaxed">{content}</p>

      <div className="flex items-center gap-2 flex-wrap">
        <EmotionBadge emotion={emotion} confidence={confidence} />
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
