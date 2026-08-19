import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import type { Trend } from "../types";

/** Daily average GCCF composite over the trailing window -- the thing a
 * flat snapshot table can't show: whether coaching is actually moving
 * scores over time. Backs the Team Roster (org-wide) and Teams overview
 * (one team at a time, via `teamId`). */
export function TrendChart({ teamId, days = 30, height = 220 }: { teamId?: string; days?: number; height?: number }) {
  const [trend, setTrend] = useState<Trend | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setTrend(null);
    setError(false);
    api
      .trend(teamId, days)
      .then(setTrend)
      .catch(() => setError(true));
  }, [teamId, days]);

  if (error) return <div className="empty-state">Could not load the trend.</div>;
  if (!trend) return <div className="loading">Loading...</div>;
  if (trend.points.length < 2) {
    return <div className="empty-state">Not enough history yet -- check back after a few days of use.</div>;
  }

  const data = trend.points.map((p) => ({
    date: new Date(p.day).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    avg_composite: p.avg_composite,
    prompt_count: p.prompt_count,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid stroke="#2a2f3a" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: "#9aa1ae", fontSize: 11 }} axisLine={{ stroke: "#2a2f3a" }} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: "#9aa1ae", fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
        <Tooltip
          contentStyle={{ background: "#1f232c", border: "1px solid #2a2f3a", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#9aa1ae" }}
          formatter={(value: number, name: string) => [value, name === "avg_composite" ? "Avg GCCF" : name]}
        />
        <ReferenceLine y={35} stroke="#f87171" strokeDasharray="4 4" />
        <Line type="monotone" dataKey="avg_composite" stroke="#6ea8fe" strokeWidth={2.5} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
