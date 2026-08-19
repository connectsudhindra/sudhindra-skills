import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
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

const DIMENSION_LINES: { key: "avg_goal" | "avg_context" | "avg_constraints" | "avg_format"; label: string; color: string }[] = [
  { key: "avg_goal", label: "Goal", color: "#6ea8fe" },
  { key: "avg_context", label: "Context", color: "#4ade80" },
  { key: "avg_constraints", label: "Constraints", color: "#fbbf24" },
  { key: "avg_format", label: "Format", color: "#c084fc" },
];

/** Per-dimension GCCF trend over the trailing window -- shows WHICH
 * dimension is moving, not just an overall average. Backs the Team Roster
 * (org-wide) and Teams overview (one team at a time, via `teamId`). */
export function TrendChart({
  teamId,
  days = 30,
  height = 240,
  showComposite = false,
}: {
  teamId?: string;
  days?: number;
  height?: number;
  showComposite?: boolean;
}) {
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
    avg_goal: p.avg_goal,
    avg_context: p.avg_context,
    avg_constraints: p.avg_constraints,
    avg_format: p.avg_format,
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
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <ReferenceLine y={35} stroke="#f87171" strokeDasharray="4 4" />
        {DIMENSION_LINES.map((d) => (
          <Line key={d.key} type="monotone" dataKey={d.key} name={d.label} stroke={d.color} strokeWidth={2} dot={{ r: 2 }} />
        ))}
        {showComposite && (
          <Line
            type="monotone"
            dataKey="avg_composite"
            name="Composite"
            stroke="#e6e8ec"
            strokeWidth={2.5}
            strokeDasharray="2 2"
            dot={false}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
