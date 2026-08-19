const LEVEL_COLORS: Record<number, string> = {
  1: "#f87171",
  2: "#fbbf24",
  3: "#a3e635",
  4: "#4ade80",
  5: "#6ea8fe",
};

export function LevelBadge({ level, name }: { level: number; name: string }) {
  const color = LEVEL_COLORS[level] ?? "#9aa1ae";
  return (
    <span className="level-badge" style={{ borderColor: color, color }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: color }} />
      L{level} {name}
    </span>
  );
}
