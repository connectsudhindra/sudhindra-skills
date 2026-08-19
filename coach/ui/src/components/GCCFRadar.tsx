import type { GCCFScore } from "../types";

const DIMENSIONS: { key: keyof Omit<GCCFScore, "rationale">; label: string }[] = [
  { key: "goal", label: "Goal" },
  { key: "context", label: "Context" },
  { key: "constraints", label: "Constraints" },
  { key: "format", label: "Format" },
];

const SIZE = 200;
const CENTER = SIZE / 2;
const RADIUS = 75;

function pointFor(index: number, total: number, value: number): [number, number] {
  const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
  const r = (value / 100) * RADIUS;
  return [CENTER + r * Math.cos(angle), CENTER + r * Math.sin(angle)];
}

/** Hand-rolled SVG radar chart -- deliberately no charting library for four
 * static points on a fixed scale; a dependency would cost more than it saves. */
export function GCCFRadar({ score }: { score: GCCFScore }) {
  const points = DIMENSIONS.map((d, i) => pointFor(i, DIMENSIONS.length, score[d.key] as number));
  const polygon = points.map(([x, y]) => `${x},${y}`).join(" ");

  const gridRings = [25, 50, 75, 100];

  return (
    <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
      {gridRings.map((ring) => (
        <circle
          key={ring}
          cx={CENTER}
          cy={CENTER}
          r={(ring / 100) * RADIUS}
          fill="none"
          stroke="#2a2f3a"
          strokeWidth={1}
        />
      ))}
      {DIMENSIONS.map((_, i) => {
        const [x, y] = pointFor(i, DIMENSIONS.length, 100);
        return <line key={i} x1={CENTER} y1={CENTER} x2={x} y2={y} stroke="#2a2f3a" strokeWidth={1} />;
      })}
      <polygon points={polygon} fill="rgba(110,168,254,0.25)" stroke="#6ea8fe" strokeWidth={2} />
      {points.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={3} fill="#6ea8fe" />
      ))}
      {DIMENSIONS.map((d, i) => {
        const [x, y] = pointFor(i, DIMENSIONS.length, 118);
        return (
          <text
            key={d.key}
            x={x}
            y={y}
            fill="#9aa1ae"
            fontSize={11}
            textAnchor="middle"
            dominantBaseline="middle"
          >
            {d.label}
          </text>
        );
      })}
    </svg>
  );
}
