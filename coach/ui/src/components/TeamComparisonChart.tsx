import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Team } from "../types";

export function TeamComparisonChart({ teams, height = 200 }: { teams: Team[]; height?: number }) {
  const data = teams
    .filter((t) => t.avg_composite != null)
    .map((t) => ({ name: t.name, avg_composite: t.avg_composite as number }));

  if (data.length === 0) {
    return <div className="empty-state">No scored prompts yet across any team.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid stroke="#2a2f3a" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: "#9aa1ae", fontSize: 11 }} axisLine={{ stroke: "#2a2f3a" }} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: "#9aa1ae", fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
        <Tooltip
          contentStyle={{ background: "#1f232c", border: "1px solid #2a2f3a", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#9aa1ae" }}
          formatter={(value: number) => [value, "Avg GCCF"]}
        />
        <Bar dataKey="avg_composite" fill="#6ea8fe" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
