import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Prompt } from "../types";

/** Composite score (heuristic) over time, oldest to newest. `prompts` is
 * expected newest-first (as the API returns it). */
export function ScoreTrend({ prompts, height = 200 }: { prompts: Prompt[]; height?: number }) {
  const data = [...prompts]
    .reverse()
    .map((p) => {
      const score = p.scores.find((s) => s.scoring_method === "heuristic")?.composite_score;
      return score == null
        ? null
        : { date: new Date(p.submitted_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }), composite: score };
    })
    .filter((v): v is { date: string; composite: number } => v != null);

  if (data.length < 2) {
    return <div className="empty-state">Not enough scored prompts yet for a trend.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
        <defs>
          <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6ea8fe" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#6ea8fe" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#2a2f3a" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: "#9aa1ae", fontSize: 11 }} axisLine={{ stroke: "#2a2f3a" }} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: "#9aa1ae", fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
        <Tooltip
          contentStyle={{ background: "#1f232c", border: "1px solid #2a2f3a", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#9aa1ae" }}
        />
        <ReferenceLine y={35} stroke="#f87171" strokeDasharray="4 4" />
        <Area type="monotone" dataKey="composite" stroke="#6ea8fe" strokeWidth={2} fill="url(#scoreFill)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
