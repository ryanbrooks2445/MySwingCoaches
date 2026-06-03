"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export function ProgressChart({
  data,
}: {
  data: { date: string; score: number }[];
}) {
  if (!data.length) {
    return (
      <p className="py-12 text-center text-[var(--color-muted)]">
        Upload swings to see your progress chart.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="var(--color-muted)" />
        <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="var(--color-muted)" />
        <Tooltip
          contentStyle={{
            background: "var(--color-card)",
            border: "1px solid var(--color-border)",
            borderRadius: 8,
          }}
        />
        <Line
          type="monotone"
          dataKey="score"
          stroke="var(--color-accent)"
          strokeWidth={2}
          dot={{ fill: "var(--color-accent)" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
