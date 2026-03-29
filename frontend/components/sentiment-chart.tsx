"use client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { tokens } from "@/lib/design-tokens";

interface DataPoint {
  index:    number;
  excited:  number;
  positive: number;
  neutral:  number;
  negative: number;
  angry:    number;
}

interface SentimentChartProps {
  data: DataPoint[];
}

const EMOTION_LINES = [
  { key: "excited",  color: tokens.emotion.excited  },
  { key: "positive", color: tokens.emotion.positive },
  { key: "neutral",  color: tokens.emotion.neutral  },
  { key: "negative", color: tokens.emotion.negative },
  { key: "angry",    color: tokens.emotion.angry    },
];

export function SentimentChart({ data }: SentimentChartProps) {
  if (data.length < 2) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
          Waiting for data...
        </p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={tokens.chart.grid} />
        <XAxis
          dataKey="index"
          tick={{ fontSize: 9, fill: tokens.chart.axis }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 9, fill: tokens.chart.axis }}
          tickLine={false}
          axisLine={false}
          domain={[0, 100]}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip
          contentStyle={{
            background:   tokens.chart.tooltip.bg,
            border:       `1px solid ${tokens.chart.tooltip.border}`,
            borderRadius: "2px",
            fontSize:     "10px",
            color:        tokens.chart.tooltip.text,
          }}
          formatter={(value: number) => [`${value.toFixed(1)}%`]}
        />
        <Legend
          wrapperStyle={{ fontSize: "9px", letterSpacing: "0.1em", textTransform: "uppercase" }}
        />
        {EMOTION_LINES.map(({ key, color }) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
