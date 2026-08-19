import type { Prompt } from "../types";

function scoreColor(value: number): string {
  if (value >= 65) return "#4ade80";
  if (value >= 35) return "#fbbf24";
  return "#f87171";
}

export function PromptHistoryTable({ prompts }: { prompts: Prompt[] }) {
  if (prompts.length === 0) {
    return <div className="empty-state">No prompts recorded yet.</div>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Prompt</th>
          <th>Method</th>
          <th>Composite</th>
          <th>Submitted</th>
        </tr>
      </thead>
      <tbody>
        {prompts.map((p) =>
          p.is_scorable && p.scores.length > 0 ? (
            p.scores.map((s) => (
              <tr key={`${p.id}-${s.scoring_method}`}>
                <td className="prompt-text" title={p.prompt_text}>
                  {p.prompt_text}
                </td>
                <td className="muted">{s.scoring_method}</td>
                <td>
                  <span style={{ color: scoreColor(s.composite_score), fontWeight: 600 }}>
                    {s.composite_score.toFixed(0)}
                  </span>
                </td>
                <td className="muted">{new Date(p.submitted_at).toLocaleString()}</td>
              </tr>
            ))
          ) : (
            <tr key={p.id}>
              <td className="prompt-text" title={p.prompt_text}>
                {p.prompt_text}
              </td>
              <td className="muted">unscored</td>
              <td className="muted">—</td>
              <td className="muted">{new Date(p.submitted_at).toLocaleString()}</td>
            </tr>
          ),
        )}
      </tbody>
    </table>
  );
}
