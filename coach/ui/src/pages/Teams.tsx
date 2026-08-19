import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { TeamComparisonChart } from "../components/TeamComparisonChart";
import { TrendChart } from "../components/TrendChart";
import type { Team } from "../types";

export function Teams() {
  const [teams, setTeams] = useState<Team[] | null>(null);
  const [selected, setSelected] = useState<Team | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listTeams()
      .then((t) => {
        setTeams(t);
        setSelected((prev) => prev ?? t[0] ?? null);
      })
      .catch(() => setError("Could not reach the coach API. Is docker compose up?"));
  }, []);

  if (error) return <div className="empty-state">{error}</div>;
  if (!teams) return <div className="loading">Loading...</div>;
  if (teams.length === 0) {
    return (
      <div className="empty-state">
        No teams yet. Run <code>docker compose exec api python seed_sample_data.py</code> for sample data.
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <p className="section-title">Teams compared — rolling GCCF composite</p>
        <TeamComparisonChart teams={teams} />
      </div>

      <div className="card">
        <p className="section-title" style={{ margin: 0 }}>
          Team roster
        </p>
        <table style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Team</th>
              <th>Members</th>
              <th>Avg level</th>
              <th>Avg GCCF</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {teams.map((t) => (
              <tr key={t.id}>
                <td>{t.name}</td>
                <td className="muted">{t.member_count}</td>
                <td className="muted">{t.avg_level != null ? t.avg_level.toFixed(1) : "—"}</td>
                <td className="muted">{t.avg_composite != null ? t.avg_composite.toFixed(0) : "—"}</td>
                <td>
                  <button className="chip" onClick={() => setSelected(t)}>
                    View trend
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <div className="card">
          <p className="section-title">{selected.name} — 30-day GCCF trend</p>
          <TrendChart teamId={selected.id} days={30} />
          <p className="muted" style={{ marginTop: 8 }}>
            <Link to={`/dashboard?team=${selected.id}`}>View {selected.name}'s roster →</Link>
          </p>
        </div>
      )}
    </div>
  );
}
