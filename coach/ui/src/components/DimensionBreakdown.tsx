import type { DimensionFeedback, DimensionKey } from "../types";

const LABELS: Record<DimensionKey, string> = {
  goal: "Goal",
  context: "Context",
  constraints: "Constraints",
  format: "Format",
};

const STATUS_COLOR: Record<string, string> = {
  strong: "#4ade80",
  developing: "#fbbf24",
  weak: "#f87171",
};

/** The core "what's wrong, what to do" surface -- one row per GCCF
 * dimension: a colored bar for the score, then (unless it's already
 * strong) the specific issue and the one thing to fix. This is what backs
 * expanded prompt rows and both the user- and team-level Progress cards. */
export function DimensionBreakdown({
  dimensions,
  order = ["goal", "context", "constraints", "format"],
}: {
  dimensions: Record<string, DimensionFeedback>;
  order?: DimensionKey[];
}) {
  return (
    <div>
      {order.map((key) => {
        const fb = dimensions[key];
        if (!fb) return null;
        const color = STATUS_COLOR[fb.status] ?? "#9aa1ae";
        return (
          <div key={key} style={{ marginBottom: 12 }}>
            <div className="dim-row">
              <span>{LABELS[key]}</span>
              <div className="score-bar-track">
                <div className="score-bar-fill" style={{ width: `${fb.score}%`, background: color }} />
              </div>
              <span style={{ color, fontWeight: 600, textAlign: "right" }}>{fb.score.toFixed(0)}</span>
            </div>
            {fb.status !== "strong" && fb.tip && (
              <div style={{ marginLeft: 98, fontSize: 13 }}>
                <span className="muted">{fb.message}.</span>
                <div style={{ color: "#6ea8fe", marginTop: 2 }}>→ {fb.tip}</div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
