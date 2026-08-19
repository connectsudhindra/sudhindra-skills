import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { LevelBadge } from "../components/LevelBadge";
import { PromptHistoryTable } from "../components/PromptHistoryTable";
import type { SessionDetail as SessionDetailData } from "../types";

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [detail, setDetail] = useState<SessionDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api
      .getSessionDetail(sessionId)
      .then(setDetail)
      .catch(() => setError("Could not load this session."));
  }, [sessionId]);

  if (error) return <div className="empty-state">{error}</div>;
  if (!detail) return <div className="loading">Loading...</div>;

  const { session, prompts } = detail;

  return (
    <div>
      <p className="muted">
        <Link to="/dashboard">← Back to roster</Link>
      </p>
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <p className="section-title" style={{ margin: 0 }}>
              Session
            </p>
            <p className="muted" style={{ margin: "4px 0 0 0" }}>
              {new Date(session.started_at).toLocaleString()}
              {session.ended_at ? ` — ${new Date(session.ended_at).toLocaleTimeString()}` : " (open)"}
            </p>
          </div>
          {session.session_level && session.session_level_name && (
            <LevelBadge level={session.session_level} name={session.session_level_name} />
          )}
        </div>
        <p className="muted" style={{ marginTop: 12 }}>
          {session.prompt_count} scored prompt(s), average GCCF{" "}
          {session.avg_composite != null ? session.avg_composite.toFixed(0) : "—"}/100
        </p>
      </div>

      <div className="card">
        <p className="section-title">Prompts in this session</p>
        <PromptHistoryTable prompts={prompts} />
      </div>
    </div>
  );
}
