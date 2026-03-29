import { emotionTextClass, emotionBorderClass } from "@/lib/design-tokens";

interface EmotionBadgeProps {
  emotion:    string;
  confidence: number;
  size?:      "sm" | "md";
}

export function EmotionBadge({ emotion, confidence, size = "sm" }: EmotionBadgeProps) {
  const textClass   = emotionTextClass[emotion]   ?? "text-muted-foreground";
  const borderClass = emotionBorderClass[emotion] ?? "border-border";

  return (
    <span
      className={`inline-flex items-center gap-1.5 border px-2.5 py-1 ${borderClass} ${textClass} ${
        size === "md" ? "text-[10px]" : "text-[9px]"
      } tracking-widest uppercase font-mono`}
    >
      {emotion}
      <span className="opacity-60">{(confidence * 100).toFixed(0)}%</span>
    </span>
  );
}
