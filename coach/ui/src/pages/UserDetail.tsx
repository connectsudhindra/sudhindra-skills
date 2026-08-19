import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { GCCFRadar } from "../components/GCCFRadar";
import { LevelBadge } from "../components/LevelBadge";
import { PromptHistoryTable } from "../components/PromptHistoryTable";
import { ScoreTrend } from "../components/ScoreTrend";
import type {
  CoachingFeedback,
  Prompt,
  UserDetail as UserDetailData,
} from "../types";

/** Shared by the admin route (/dashboard/users/:id) and the personal route
 * (/me, which resolves its own id first -- see MyCoaching.tsx) so both stay
 * in sync with one implementation rather than two. `showAdminHint` just
 * toggles a one-line note; there are no actual admin controls to hide here
 * in v1 (see coach/README.md on auth). */
export function UserDetailView({ userId, showAdminHint = true }: { userId: string; showAdminHint?: boolean }) {
  const [detail, setDetail] = useState<UserDetailData | null>(null);
  const [prompts, setPrompts] = useState<Prompt[] | null>(null);
  const [feedback, setFeedback] = useState<CoachingFeedback[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDetail(null);
    setPrompts(null);
    Promise.all([
      api.getUserDetail(userId),
      api.getUserPrompts(userId, 50, 0),
      api.getUserFeedback(userId).catch(() => []),
    ])
      .then(([d, p, f]) => {
        setDetail(d);
        setPrompts(p);
        setFeedback(f);
      })
      .catch(() => setError("Could not load this user."));
  }, [userId]);

  if (error) return <div className="empty-state">{error}</div>;
  if (!detail || !prompts) return <div className="loading">Loading...</div>;

  const { user, level_history, gccf_averages } = detail;

  return (
    <div>
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h2 style={{ margin: "0 0 6px 0" }}>{user.name}</h2>
            <p className="muted" style={{ margin: 0 }}>
              {user.email}
            </p>
          </div>
          <LevelBadge level={user.current_level} name={user.current_level_name} />
        </div>

        {showAdminHint && (
          <p className="muted" style={{ marginTop: 12 }}>
            Rolling composite: {user.rolling_composite != null ? user.rolling_composite.toFixed(0) : "—"}/100
            over the last {user.scorable_prompt_count} scored prompt(s). Coaching mode:{" "}
            {user.coaching_mode}.
          </p>
        )}
      </div>

      <div className="card" style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
        <div>
          <p className="section-title">GCCF averages</p>
          {gccf_averages ? (
            <GCCFRadar score={gccf_averages} />
          ) : (
            <div className="empty-state">No scored prompts yet.</div>
          )}
        </div>
        <div style={{ flex: 1, minWidth: 280 }}>
          <p className="section-title">Composite trend</p>
          <ScoreTrend prompts={prompts} />
          <p className="muted" style={{ marginTop: 8 }}>
            Dashed line marks the default in-session block floor (35/100).
          </p>
        </div>
      </div>

      {level_history.length > 0 && (
        <div className="card">
          <p className="section-title">Level history</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {level_history.map((h, i) => (
              <span key={i} className="muted">
                L{h.level_num} on {new Date(h.achieved_at).toLocaleDateString()}
                {i < level_history.length - 1 ? " →" : ""}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <p className="section-title">Prompt history</p>
        <PromptHistoryTable prompts={prompts} />
      </div>

      {feedback.length > 0 && (
        <div className="card">
          <p className="section-title">Recent coaching feedback</p>
          {feedback.map((f) => (
            <div key={f.id} style={{ marginBottom: 10 }}>
              <span className="muted">
                {f.feedback_type} · {new Date(f.created_at).toLocaleString()}
              </span>
              <p style={{ margin: "4px 0 0 0" }}>{f.feedback_text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function UserDetailPage() {
  const { userId } = useParams<{ userId: string }>();
  if (!userId) return <div className="empty-state">No user selected.</div>;
  return <UserDetailView userId={userId} />;
}
