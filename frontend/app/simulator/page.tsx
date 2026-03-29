"use client";
import { useState, useEffect, useRef } from "react";
import { TopNav }             from "@/components/top-nav";
import { WarmingUp }          from "@/components/warming-up";
import { FeedPost }           from "@/components/feed-post";
import { AlertBanner }        from "@/components/alert-banner";
import { EditorialGuardrail } from "@/components/editorial-guardrail";
import { narrativeArc }       from "@/lib/design-tokens";
import { healthCheck, startFeed, getNextBatch, getStats } from "@/lib/api";

type Post = {
  content:    string;
  emotion:    string;
  confidence: number;
  topics:     Array<{ topic: string; confidence: number }>;
  shap_words: string[];
  source:     string;
  stage?:     string;
};

type Stats = {
  total:        number;
  emotion_pct:  Record<string, number>;
  topic_counts: Record<string, number>;
  alert:        { type: string; pct: number; dominant_topic: string; message: string } | null;
};

export default function Simulator() {
  const [ready,   setReady]   = useState(false);
  const [posts,   setPosts]   = useState<Post[]>([]);
  const [stats,   setStats]   = useState<Stats | null>(null);
  const [running, setRunning] = useState(false);
  const [stage,   setStage]   = useState("opening");
  const feedRef   = useRef<NodeJS.Timeout | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const check = async () => {
      let ok = false;
      for (let i = 0; i < 25; i++) {
        ok = await healthCheck();
        if (ok) break;
        await new Promise(r => setTimeout(r, 4000));
      }
      setReady(ok);
    };
    check();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [posts]);

  const handleStart = async () => {
    await startFeed();
    setPosts([]);
    setStats(null);
    setStage("opening");
    setRunning(true);
  };

  const handleStop = () => {
    setRunning(false);
    if (feedRef.current) clearInterval(feedRef.current);
  };

  useEffect(() => {
    if (!running) return;
    const tick = async () => {
      try {
        const batch = await getNextBatch(2);
        setPosts(prev => [...prev.slice(-60), ...batch.posts]);
        setStage(batch.current_stage ?? "opening");
        const s = await getStats();
        setStats(s);
      } catch {
        // silent
      }
    };
    tick();
    feedRef.current = setInterval(tick, 2500);
    return () => { if (feedRef.current) clearInterval(feedRef.current); };
  }, [running]);

  const currentArc = narrativeArc.find(a => a.stage === stage);

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      <TopNav />

      {!ready ? (
        <div className="flex-1 flex items-center justify-center">
          <WarmingUp />
        </div>
      ) : (
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* Simulation header */}
          <div className="border-b border-border px-5 py-3 flex items-center justify-between shrink-0">
            <div className="space-y-0.5">
              <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
                BAFTA 2026 — SCRIPTED SIMULATION
              </p>
              {currentArc && (
                <p className="text-xs text-foreground">
                  <span className="text-primary font-mono uppercase text-[9px] tracking-widest mr-2">
                    {currentArc.label}
                  </span>
                  <span className="text-muted-foreground text-[9px]">
                    dominant: {currentArc.dominant}
                  </span>
                </p>
              )}
            </div>
            <button
              onClick={running ? handleStop : handleStart}
              className={`px-5 py-2 text-[10px] tracking-widest uppercase border transition-colors ${
                running
                  ? "border-destructive text-destructive hover:bg-destructive hover:text-background"
                  : "border-primary text-primary hover:bg-primary hover:text-primary-foreground"
              }`}
            >
              {running ? "STOP" : "RUN BAFTA NIGHT"}
            </button>
          </div>

          {/* Narrative arc stages */}
          <div className="border-b border-border px-5 py-2 flex items-center gap-6 shrink-0 overflow-x-auto scrollbar-hide">
            {narrativeArc.map(arc => (
              <div
                key={arc.stage}
                className={`flex items-center gap-1.5 shrink-0 transition-opacity ${
                  arc.stage === stage ? "opacity-100" : "opacity-30"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full bg-emotion-${arc.dominant}`}
                />
                <span className="text-[9px] tracking-widest uppercase text-foreground">
                  {arc.label}
                </span>
              </div>
            ))}
          </div>

          <div className="flex-1 flex overflow-hidden">

            {/* Feed */}
            <div className="flex-1 flex flex-col overflow-hidden border-r border-border">
              {stats?.alert && (
                <div className="px-4 pt-3 shrink-0">
                  <AlertBanner
                    pct={stats.alert.pct}
                    dominantTopic={stats.alert.dominant_topic}
                    message={stats.alert.message}
                  />
                </div>
              )}
              <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide"
              >
                {posts.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
                      Press RUN BAFTA NIGHT to begin
                    </p>
                  </div>
                ) : (
                  posts.map((post, i) => (
                    <FeedPost key={i} {...post} />
                  ))
                )}
              </div>
            </div>

            {/* Stats sidebar */}
            <div className="w-64 shrink-0 p-4 space-y-4 overflow-y-auto">
              <div>
                <p className="text-[9px] tracking-widest text-muted-foreground uppercase mb-2">
                  EMOTION SPLIT
                </p>
                {stats ? (
                  <div className="space-y-1.5">
                    {Object.entries(stats.emotion_pct)
                      .sort((a, b) => b[1] - a[1])
                      .map(([emotion, pct]) => (
                        <div key={emotion} className="flex items-center justify-between">
                          <span className={`text-[9px] uppercase tracking-widest text-emotion-${emotion}`}>
                            {emotion}
                          </span>
                          <span className="font-mono text-[9px] text-muted-foreground tabular-nums">
                            {pct.toFixed(1)}%
                          </span>
                        </div>
                      ))}
                  </div>
                ) : (
                  <p className="text-[9px] text-muted-foreground">No data</p>
                )}
              </div>

              <div className="border-t border-border pt-4">
                <p className="text-[9px] tracking-widest text-muted-foreground uppercase mb-2">
                  POSTS CLASSIFIED
                </p>
                <p className="font-mono text-lg text-foreground tabular-nums">
                  {stats?.total ?? 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      <EditorialGuardrail />
    </div>
  );
}
