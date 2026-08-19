import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { DimensionKey, Progress } from "../types";

const LABELS: Record<DimensionKey, string> = {
  goal: "Goal",
  context: "Context",
  constraints: "Constraints",
  format: "Format",
};

const DIRECTION_ICON: Record<string, string> = { improving: "↑", declining: "↓", flat: "→" };
const DIRECTION_COLOR: Record<string, string> = { improving: "#4ade80", declining: "#f87171", flat: "#9aa1ae" };

/** Answers "is this person/team actually getting better" -- recent window
 * vs. the window before it, per dimension, plus the single most common
 * reason a still-weak dimension is weak. Shared by user and team detail
 * views via `scope` (either `{ userId }` or `{ teamId }`). */
export function ProgressCard({ userId, teamId }: { userId?: string; teamId?: string }) {
  const [progress, setProgress] = useState<Progress | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setProgress(null);
    setError(null);
    const request = userId ? api.getUserProgress(userId) : teamId ? api.getTeamProgress(teamId) : null;
    request?.then(setProgress).catch(() => setError("Could not load progress."));
  }, [userId, teamId]);

  if (error) return <div className="empty-state">{error}</div>;
  if (!progress) return <div className="loading">Loading...</div>;

  const hasData = progress.dimensions.some((d) => d.recent_avg != null);

  return (
    <div>
      <p style={{ marginTop: 0 }}>{progress.headline}</p>
      {hasData && (
        <table>
          <thead>
            <tr>
              <th>Dimension</th>
              <th>Recent avg</th>
              <th>Prior avg</th>
              <th>Change</th>
              <th>Most common issue</th>
            </tr>
          </thead>
          <tbody>
            {progress.dimensions.map((d) => (
              <tr key={d.dimension}>
                <td>{LABELS[d.dimension]}</td>
                <td>{d.recent_avg != null ? d.recent_avg.toFixed(0) : "—"}</td>
                <td className="muted">{d.prior_avg != null ? d.prior_avg.toFixed(0) : "—"}</td>
                <td style={{ color: DIRECTION_COLOR[d.direction] }}>
                  {d.delta != null ? `${DIRECTION_ICON[d.direction]} ${Math.abs(d.delta).toFixed(0)}` : "—"}
                </td>
                <td className="muted">
                  {d.most_common_issue_message ? (
                    <>
                      {d.most_common_issue_message}
                      {d.tip && <div style={{ color: "#6ea8fe", marginTop: 2 }}>→ {d.tip}</div>}
                    </>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
