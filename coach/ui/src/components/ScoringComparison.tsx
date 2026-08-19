import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ScoringComparison as ScoringComparisonData } from "../types";

/** Heuristic-vs-LLM agreement panel -- lives on Team Roster and User Detail,
 * not its own route, per the "don't over-design" scope for this dashboard. */
export function ScoringComparison() {
  const [data, setData] = useState<ScoringComparisonData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .scoringComparison()
      .then(setData)
      .catch(() => setError("Could not load scoring comparison."));
  }, []);

  if (error) return <div className="muted">{error}</div>;
  if (!data) return <div className="loading">Loading...</div>;

  if (data.sample_size === 0) {
    return (
      <div className="empty-state">
        No prompts scored by both methods yet -- set ANTHROPIC_API_KEY to enable LLM comparison
        scoring.
      </div>
    );
  }

  return (
    <div>
      <p className="muted" style={{ marginTop: 0 }}>
        {data.sample_size} prompt(s) scored by both methods. Mean absolute difference:{" "}
        <strong style={{ color: "var(--text)" }}>{data.mean_abs_diff}</strong> points.
      </p>
      <table>
        <thead>
          <tr>
            <th>Heuristic</th>
            <th>LLM</th>
            <th>Diff</th>
          </tr>
        </thead>
        <tbody>
          {data.pairs.slice(0, 10).map((pair, i) => (
            <tr key={i}>
              <td>{pair.heuristic_composite.toFixed(0)}</td>
              <td>{pair.llm_composite.toFixed(0)}</td>
              <td className="muted">
                {Math.abs(pair.heuristic_composite - pair.llm_composite).toFixed(0)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
