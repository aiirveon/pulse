/**
 * design-tokens.ts
 * ─────────────────
 * Single source of truth for design token values used in TypeScript/TSX.
 * All values mirror styles/tokens.css exactly.
 * Use these for recharts stroke/fill props — never hardcode hex values.
 *
 * Rule: if it's a Tailwind className context → use the Tailwind token class
 *       if it's a JS/TS prop (chart colour, inline style) → use this file
 */

export const tokens = {
  emotion: {
    excited:  "var(--emotion-excited)",
    positive: "var(--emotion-positive)",
    neutral:  "var(--emotion-neutral)",
    negative: "var(--emotion-negative)",
    angry:    "var(--emotion-angry)",
  },
  chart: {
    grid:   "var(--border)",
    axis:   "var(--muted-foreground)",
    tooltip: {
      bg:     "var(--panel-dark)",
      border: "var(--border)",
      text:   "var(--foreground)",
    },
  },
  score: {
    high: "var(--score-high)",
    mid:  "var(--score-mid)",
    low:  "var(--score-low)",
  },
  primary:    "var(--primary)",
  border:     "var(--border)",
  foreground: "var(--foreground)",
  muted:      "var(--muted-foreground)",
  panel:      "var(--panel)",
  panelDark:  "var(--panel-dark)",
  alert: {
    bg:     "var(--alert-bg)",
    border: "var(--alert-border)",
  },
} as const

/** Maps emotion label → Tailwind text class. Use in JSX className props. */
export const emotionTextClass: Record<string, string> = {
  excited:  "text-emotion-excited",
  positive: "text-emotion-positive",
  neutral:  "text-emotion-neutral",
  negative: "text-emotion-negative",
  angry:    "text-emotion-angry",
}

/** Maps emotion label → Tailwind border class. Use for badge borders. */
export const emotionBorderClass: Record<string, string> = {
  excited:  "border-emotion-excited",
  positive: "border-emotion-positive",
  neutral:  "border-emotion-neutral",
  negative: "border-emotion-negative",
  angry:    "border-emotion-angry",
}

/** Maps topic label → display name. */
export const topicDisplayName: Record<string, string> = {
  winner_reaction:         "Winner Reaction",
  presenter_performance:   "Presenter Performance",
  ceremony_production:     "Ceremony Production",
  diversity_representation:"Diversity & Representation",
  fashion_red_carpet:      "Fashion & Red Carpet",
  general_audience_reaction:"General Audience",
}

/** Narrative arc stages — matches generate_dataset.py NARRATIVE_ARC */
export const narrativeArc = [
  { stage: "opening",      label: "OPENING",       dominant: "excited" },
  { stage: "early_awards", label: "EARLY AWARDS",  dominant: "positive" },
  { stage: "controversy",  label: "CONTROVERSY",   dominant: "negative" },
  { stage: "recovery",     label: "RECOVERY",      dominant: "excited" },
  { stage: "closing",      label: "CLOSING",       dominant: "positive" },
] as const
