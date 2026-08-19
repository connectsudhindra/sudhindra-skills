import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { LevelDistributionEntry } from "../types";

const LEVEL_COLORS: Record<number, string> = {
  1: "#f87171",
  2: "#fbbf24",
  3: "#a3e635",
  4: "#4ade80",
  5: "#6ea8fe",
};

export function LevelDistributionChart({ data, height = 180 }: { data: LevelDistributionEntry[]; height?: number }) {
  const chartData = data.map((d) => ({ name: d.name, count: d.user_count, level: d.level_num }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 8, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid stroke="#2a2f3a" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: "#9aa1ae", fontSize: 11 }} axisLine={{ stroke: "#2a2f3a" }} tickLine={false} />
        <YAxis allowDecimals={false} tick={{ fill: "#9aa1ae", fontSize: 11 }} axisLine={false} tickLine={false} width={24} />
        <Tooltip
          contentStyle={{ background: "#1f232c", border: "1px solid #2a2f3a", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#9aa1ae" }}
          formatter={(value: number) => [value, "Users"]}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {chartData.map((entry) => (
            <Cell key={entry.level} fill={LEVEL_COLORS[entry.level] ?? "#9aa1ae"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
