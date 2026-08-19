import type { Prompt } from "../types";

const WIDTH = 480;
const HEIGHT = 100;
const PADDING = 8;

/** Composite score (heuristic) over time, oldest to newest, as a plain SVG
 * sparkline. `prompts` is expected newest-first (as the API returns it). */
export function ScoreTrend({ prompts }: { prompts: Prompt[] }) {
  const points = [...prompts]
    .reverse()
    .map((p) => p.scores.find((s) => s.scoring_method === "heuristic")?.composite_score)
    .filter((v): v is number => v != null);

  if (points.length < 2) {
    return <div className="empty-state">Not enough scored prompts yet for a trend.</div>;
  }

  const stepX = (WIDTH - PADDING * 2) / (points.length - 1);
  const toY = (v: number) => HEIGHT - PADDING - (v / 100) * (HEIGHT - PADDING * 2);

  const path = points
    .map((v, i) => `${i === 0 ? "M" : "L"} ${PADDING + i * stepX} ${toY(v)}`)
    .join(" ");

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`}>
      <line
        x1={PADDING}
        y1={toY(35)}
        x2={WIDTH - PADDING}
        y2={toY(35)}
        stroke="#f87171"
        strokeDasharray="4 4"
        strokeWidth={1}
      />
      <path d={path} fill="none" stroke="#6ea8fe" strokeWidth={2} />
      {points.map((v, i) => (
        <circle key={i} cx={PADDING + i * stepX} cy={toY(v)} r={2.5} fill="#6ea8fe" />
      ))}
    </svg>
  );
}
