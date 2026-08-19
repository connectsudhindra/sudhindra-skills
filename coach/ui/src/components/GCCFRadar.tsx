import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import type { GCCFScore } from "../types";

export function GCCFRadar({ score, height = 220 }: { score: GCCFScore; height?: number }) {
  const data = [
    { dimension: "Goal", value: score.goal },
    { dimension: "Context", value: score.context },
    { dimension: "Constraints", value: score.constraints },
    { dimension: "Format", value: score.format },
  ];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} outerRadius="75%">
        <PolarGrid stroke="#2a2f3a" />
        <PolarAngleAxis dataKey="dimension" tick={{ fill: "#9aa1ae", fontSize: 12 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#565d6b", fontSize: 10 }} />
        <Radar
          dataKey="value"
          stroke="#6ea8fe"
          fill="#6ea8fe"
          fillOpacity={0.28}
          strokeWidth={2}
          dot={{ r: 3, fill: "#6ea8fe" }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
