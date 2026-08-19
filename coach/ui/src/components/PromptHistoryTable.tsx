import { Fragment, useState } from "react";
import { DimensionBreakdown } from "./DimensionBreakdown";
import type { Prompt } from "../types";

function scoreColor(value: number): string {
  if (value >= 65) return "#4ade80";
  if (value >= 35) return "#fbbf24";
  return "#f87171";
}

/** Each row expands into the full GCCF breakdown for that prompt -- not
 * just the composite number, the specific issue per dimension and the one
 * thing to fix, straight from the heuristic scorer's stored
 * dimension_feedback. This is the "what did I do wrong, what do I do about
 * it" view at the level of one actual prompt. */
export function PromptHistoryTable({ prompts }: { prompts: Prompt[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (prompts.length === 0) {
    return <div className="empty-state">No prompts recorded yet.</div>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th></th>
          <th>Prompt</th>
          <th>Method</th>
          <th>Composite</th>
          <th>Submitted</th>
        </tr>
      </thead>
      <tbody>
        {prompts.map((p) => {
          const heuristic = p.scores.find((s) => s.scoring_method === "heuristic");
          const isOpen = expanded === p.id;
          const canExpand = p.is_scorable && heuristic?.dimension_feedback != null;

          return (
            <Fragment key={p.id}>
              <tr
                onClick={() => canExpand && setExpanded(isOpen ? null : p.id)}
                style={canExpand ? { cursor: "pointer" } : undefined}
              >
                <td className="muted">{canExpand ? (isOpen ? "▾" : "▸") : ""}</td>
                <td className="prompt-text" title={p.prompt_text}>
                  {p.prompt_text}
                </td>
                <td className="muted">{p.is_scorable ? (heuristic ? "heuristic" : "pending") : "unscored"}</td>
                <td>
                  {heuristic ? (
                    <span style={{ color: scoreColor(heuristic.composite_score), fontWeight: 600 }}>
                      {heuristic.composite_score.toFixed(0)}
                    </span>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td className="muted">{new Date(p.submitted_at).toLocaleString()}</td>
              </tr>
              {isOpen && heuristic?.dimension_feedback && (
                <tr key={`${p.id}-detail`}>
                  <td></td>
                  <td colSpan={4} style={{ paddingBottom: 20 }}>
                    <DimensionBreakdown dimensions={heuristic.dimension_feedback} />
                    {p.scores.some((s) => s.scoring_method === "llm") && (
                      <p className="muted" style={{ marginTop: 8 }}>
                        LLM composite:{" "}
                        {p.scores.find((s) => s.scoring_method === "llm")?.composite_score.toFixed(0)}
                      </p>
                    )}
                  </td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
