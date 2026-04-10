"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import { TopNav }             from "@/components/top-nav";
import { WarmingUp }          from "@/components/warming-up";
import { AlertBanner }        from "@/components/alert-banner";
import { FeedPost }           from "@/components/feed-post";
import { SentimentChart }     from "@/components/sentiment-chart";
import { TopicBars }          from "@/components/topic-bars";
import { EditorialGuardrail } from "@/components/editorial-guardrail";
import { healthCheck, classifyPost, startFeed, getNextBatch, getStats } from "@/lib/api";

type Post = {
  content:    string;
  emotion:    string;
  confidence: number;
  topics:     Array<{ topic: string; confidence: number }>;
  shap_words: string[];
  source:     string;
};

type ChartPoint = {
  index:    number;
  excited:  number;
  positive: number;
  neutral:  number;
  negative: number;
  angry:    number;
};

type Stats = {
  total:            number;
  emotion_pct:      Record<string, number>;
  topic_counts:     Record<string, number>;
  alert:            { type: string; pct: number; dominant_topic: string; message: string } | null;
  dominant_emotion: string | null;
};

export default function LiveMonitor() {
  const [ready,       setReady]       = useState(false);
  const [posts,       setPosts]       = useState<Post[]>([]);
  const [chartData,   setChartData]   = useState<ChartPoint[]>([]);
  const [stats,       setStats]       = useState<Stats | null>(null);
  const [running,     setRunning]     = useState(false);
  const [inputValue,  setInputValue]  = useState("");
  const [isClassifying, setIsClassifying] = useState(false);
  const feedRef   = useRef<NodeJS.Timeout | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Cold start health check
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

  // Auto-scroll feed
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [posts]);

  const refreshStats = useCallback(async () => {
    try {
      const s = await getStats();
      setStats(s);
      setChartData(prev => {
        const point: ChartPoint = {
          index:    prev.length,
          excited:  s.emotion_pct.excited  ?? 0,
          positive: s.emotion_pct.positive ?? 0,
          neutral:  s.emotion_pct.neutral  ?? 0,
          negative: s.emotion_pct.negative ?? 0,
          angry:    s.emotion_pct.angry    ?? 0,
        };
        return [...prev.slice(-30), point];
      });
    } catch {
      // silent
    }
  }, []);

  const handleStartFeed = async () => {
    if (!ready) return;
    await startFeed();
    setPosts([]);
    setChartData([]);
    setStats(null);
    setRunning(true);
  };

  const handleStopFeed = () => {
    setRunning(false);
    if (feedRef.current) clearInterval(feedRef.current);
  };

  // Feed polling interval
  useEffect(() => {
    if (!running) return;
    const tick = async () => {
      try {
        const batch = await getNextBatch(2);
        setPosts(prev => [...prev.slice(-80), ...batch.posts]);
        await refreshStats();
      } catch {
        // silent
      }
    };
    tick();
    feedRef.current = setInterval(tick, 3000);
    return () => { if (feedRef.current) clearInterval(feedRef.current); };
  }, [running, refreshStats]);

  const handleManualSubmit = async () => {
    if (!inputValue.trim() || !ready || isClassifying) return;
    setIsClassifying(true);
    try {
      const result = await classifyPost(inputValue.trim());
      setPosts(prev => [...prev.slice(-80), result]);
      await refreshStats();
      setInputValue("");
    } catch {
      // silent
    } finally {
      setIsClassifying(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleManualSubmit();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      <TopNav />

      {!ready ? (
        <div className="flex-1 flex items-center justify-center">
          <WarmingUp />
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden">

          {/* Left — feed + input */}
          <div className="flex flex-col w-1/2 border-r border-border overflow-hidden">

            {/* Feed header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
              <div>
                <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
                  LIVE FEED
                </p>
                {stats && (
                  <p className="text-[9px] text-muted-foreground font-mono mt-0.5">
                    {stats.total} posts classified
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {running && (
                  <span className="flex items-center gap-1.5 text-[9px] tracking-widest uppercase text-primary">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary status-pulse" />
                    LIVE
                  </span>
                )}
                <button
                  onClick={running ? handleStopFeed : handleStartFeed}
                  className={`px-4 py-1.5 text-[9px] tracking-widest uppercase border transition-colors ${
                    running
                      ? "border-destructive text-destructive hover:bg-destructive hover:text-background"
                      : "border-primary text-primary hover:bg-primary hover:text-primary-foreground"
                  }`}
                >
                  {running ? "STOP" : "START SIMULATION"}
                </button>
              </div>
            </div>

            {/* Alert */}
            {stats?.alert && (
              <div className="px-4 pt-3 shrink-0">
                <AlertBanner
                  pct={stats.alert.pct}
                  message={stats.alert.message}
                />
              </div>
            )}

            {/* Posts */}
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide"
            >
              {posts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-3">
                  <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
                    No posts yet
                  </p>
                  <p className="text-xs text-muted-foreground text-center max-w-xs">
                    Start the simulation or type a post below
                  </p>
                </div>
              ) : (
                posts.map((post, i) => (
                  <FeedPost key={i} {...post} />
                ))
              )}
            </div>

            {/* Manual input */}
            <div className="border-t border-border bg-panel-dark p-4 shrink-0">
              <div className="flex gap-3 items-end">
                <textarea
                  value={inputValue}
                  onChange={e => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={!ready || isClassifying}
                  placeholder="Type a BAFTA social post to classify manually..."
                  rows={2}
                  className="flex-1 bg-background border border-border text-sm text-foreground placeholder:text-muted-foreground p-3 resize-none focus:outline-none focus:border-primary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                />
                <button
                  onClick={handleManualSubmit}
                  disabled={!inputValue.trim() || !ready || isClassifying}
                  className="h-[64px] px-5 bg-primary text-primary-foreground text-[10px] font-medium tracking-[0.2em] uppercase hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                >
                  {isClassifying ? "..." : "CLASSIFY"}
                </button>
              </div>
            </div>
          </div>

          {/* Right — chart + topics */}
          <div className="flex flex-col w-1/2 overflow-hidden">

            {/* Sentiment chart */}
            <div className="flex flex-col p-4 border-b border-border" style={{ height: "260px" }}>
              <p className="text-[10px] tracking-widest text-muted-foreground uppercase mb-3 shrink-0">
                SENTIMENT OVER TIME
              </p>
              <div className="flex-1">
                {chartData.length >= 5 ? (
                  <SentimentChart data={chartData} />
                ) : (
                  <div className="h-full flex flex-col items-center justify-center gap-2">
                    <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
                      WAITING FOR DATA
                    </p>
                    <p className="text-[9px] text-muted-foreground/60">
                      {chartData.length === 0
                        ? "Start the simulation or classify posts to begin"
                        : `${chartData.length} of 5 data points collected`}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Dominant emotion */}
            {stats?.dominant_emotion && (
              <div className="px-4 py-3 border-b border-border shrink-0">
                <p className="text-[9px] tracking-widest text-muted-foreground uppercase mb-1">
                  DOMINANT EMOTION
                </p>
                <p className={`text-sm font-mono uppercase tracking-widest text-emotion-${stats.dominant_emotion}`}>
                  {stats.dominant_emotion}
                  <span className="text-muted-foreground text-[10px] ml-2">
                    {stats.emotion_pct[stats.dominant_emotion]?.toFixed(1)}%
                  </span>
                </p>
              </div>
            )}

            {/* Topic breakdown */}
            <div className="flex-1 overflow-y-auto scrollbar-hide p-4">
              <p className="text-[10px] tracking-widest text-muted-foreground uppercase mb-3">
                TOPIC BREAKDOWN
              </p>
              <TopicBars topicCounts={stats?.topic_counts ?? {}} />
            </div>
          </div>
        </div>
      )}

      <EditorialGuardrail />
    </div>
  );
}
