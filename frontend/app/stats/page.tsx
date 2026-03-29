"use client";
import { useState, useEffect } from "react";
import { TopNav }             from "@/components/top-nav";
import { WarmingUp }          from "@/components/warming-up";
import { SentimentChart }     from "@/components/sentiment-chart";
import { TopicBars }          from "@/components/topic-bars";
import { EditorialGuardrail } from "@/components/editorial-guardrail";
import { healthCheck, getStats } from "@/lib/api";

export default function StatsPage() {
  const [ready, setReady]   = useState(false);
  const [stats, setStats]   = useState<any>(null);

  useEffect(() => {
    const check = async () => {
      let ok = false;
      for (let i = 0; i < 25; i++) {
        ok = await healthCheck();
        if (ok) break;
        await new Promise(r => setTimeout(r, 4000));
      }
      setReady(ok);
      if (ok) {
        const s = await getStats();
        setStats(s);
      }
    };
    check();
  }, []);

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      <TopNav />

      {!ready ? (
        <div className="flex-1 flex items-center justify-center">
          <WarmingUp />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto scrollbar-hide p-6 space-y-6">

          <div>
            <p className="text-[10px] tracking-widest text-muted-foreground uppercase mb-1">
              SESSION OVERVIEW
            </p>
            <p className="font-mono text-3xl text-foreground tabular-nums">
              {stats?.total ?? 0}
            </p>
            <p className="text-[9px] text-muted-foreground mt-0.5">posts classified this session</p>
          </div>

          {/* Emotion breakdown */}
          <div className="bg-panel border border-border p-4 space-y-3">
            <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
              EMOTION BREAKDOWN
            </p>
            {stats ? (
              <div className="grid grid-cols-5 gap-3">
                {Object.entries(stats.emotion_pct as Record<string, number>).map(([emotion, pct]) => (
                  <div key={emotion} className="text-center space-y-1">
                    <p className={`font-mono text-xl tabular-nums text-emotion-${emotion}`}>
                      {pct.toFixed(1)}%
                    </p>
                    <p className="text-[9px] tracking-widest uppercase text-muted-foreground">
                      {emotion}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[10px] text-muted-foreground">
                Run the simulator to generate stats
              </p>
            )}
          </div>

          {/* Topic breakdown */}
          <div className="bg-panel border border-border p-4 space-y-3">
            <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
              TOPIC BREAKDOWN
            </p>
            <TopicBars topicCounts={stats?.topic_counts ?? {}} />
          </div>

          {/* Model info */}
          <div className="bg-panel border border-border p-4 space-y-3">
            <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
              MODEL INFO
            </p>
            <div className="space-y-1.5">
              {[
                ["Architecture",    "TF-IDF + XGBoost"],
                ["Emotion model",   "5-class, Macro F1 0.830"],
                ["Topic model",     "6-class multi-label, OneVsRest"],
                ["Training data",   "2,699 synthetic BAFTA posts"],
                ["Known limit",     "negative/angry boundary F1 0.750"],
              ].map(([label, value]) => (
                <div key={label} className="flex items-start gap-4">
                  <span className="text-[9px] tracking-widest uppercase text-muted-foreground w-32 shrink-0">
                    {label}
                  </span>
                  <span className="text-[10px] text-foreground font-mono">{value}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

      <EditorialGuardrail />
    </div>
  );
}
