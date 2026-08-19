import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { LevelBadge } from "../components/LevelBadge";
import { LevelDistributionChart } from "../components/LevelDistributionChart";
import { ScoringComparison } from "../components/ScoringComparison";
import { TrendChart } from "../components/TrendChart";
import type { LevelDistributionEntry, Team, UserSummary } from "../types";

export function TeamRoster() {
  const [searchParams] = useSearchParams();
  const [users, setUsers] = useState<UserSummary[] | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [distribution, setDistribution] = useState<LevelDistributionEntry[]>([]);
  const [levelFilter, setLevelFilter] = useState<number | null>(null);
  const [teamFilter, setTeamFilter] = useState<string | null>(searchParams.get("team"));
  const [sortBy, setSortBy] = useState<"composite" | "level">("level");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.levelDistribution().then(setDistribution).catch(() => {});
    api.listTeams().then(setTeams).catch(() => {});
  }, []);

  useEffect(() => {
    setUsers(null);
    api
      .listUsers(levelFilter ?? undefined, teamFilter ?? undefined)
      .then(setUsers)
      .catch(() => setError("Could not reach the coach API. Is docker compose up?"));
  }, [levelFilter, teamFilter]);

  const sorted = users
    ? [...users].sort((a, b) =>
        sortBy === "level"
          ? b.current_level - a.current_level
          : (b.rolling_composite ?? -1) - (a.rolling_composite ?? -1),
      )
    : [];

  return (
    <div>
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <p className="section-title" style={{ margin: 0 }}>
            Org-wide GCCF trend {teamFilter ? `— ${teams.find((t) => t.id === teamFilter)?.name ?? ""}` : ""}
            (30 days)
          </p>
        </div>
        <TrendChart teamId={teamFilter ?? undefined} days={30} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div className="card">
          <p className="section-title">Level distribution</p>
          <LevelDistributionChart data={distribution} />
        </div>
        <div className="card">
          <p className="section-title">Scoring comparison (heuristic vs. LLM)</p>
          <ScoringComparison />
        </div>
      </div>

      <div className="filter-chips">
        <button className={`chip ${levelFilter === null ? "active" : ""}`} onClick={() => setLevelFilter(null)}>
          All levels ({distribution.reduce((sum, d) => sum + d.user_count, 0)})
        </button>
        {distribution.map((d) => (
          <button
            key={d.level_num}
            className={`chip ${levelFilter === d.level_num ? "active" : ""}`}
            onClick={() => setLevelFilter(d.level_num)}
          >
            {d.name} ({d.user_count})
          </button>
        ))}
      </div>

      {teams.length > 0 && (
        <div className="filter-chips">
          <button className={`chip ${teamFilter === null ? "active" : ""}`} onClick={() => setTeamFilter(null)}>
            All teams
          </button>
          {teams.map((t) => (
            <button
              key={t.id}
              className={`chip ${teamFilter === t.id ? "active" : ""}`}
              onClick={() => setTeamFilter(t.id)}
            >
              {t.name} ({t.member_count})
            </button>
          ))}
        </div>
      )}

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <p className="section-title" style={{ margin: 0 }}>
            Team roster
          </p>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as "composite" | "level")}>
            <option value="level">Sort by level</option>
            <option value="composite">Sort by rolling score</option>
          </select>
        </div>

        {error && <div className="empty-state">{error}</div>}
        {!error && !users && <div className="loading">Loading...</div>}
        {!error && users && users.length === 0 && (
          <div className="empty-state">
            No users yet. Run <code>docker compose exec api python seed_sample_data.py</code> for sample data.
          </div>
        )}

        {!error && users && users.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Team</th>
                <th>Level</th>
                <th>Rolling GCCF</th>
                <th>Scored prompts</th>
                <th>Coaching mode</th>
                <th>Last active</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((u) => (
                <tr key={u.id}>
                  <td>
                    <Link to={`/dashboard/users/${u.id}`}>{u.name}</Link>
                    <div className="muted">{u.email}</div>
                  </td>
                  <td className="muted">{u.team_name ?? "—"}</td>
                  <td>
                    <LevelBadge level={u.current_level} name={u.current_level_name} />
                  </td>
                  <td>{u.rolling_composite != null ? u.rolling_composite.toFixed(0) : "—"}</td>
                  <td className="muted">{u.scorable_prompt_count}</td>
                  <td className="muted">{u.coaching_mode}</td>
                  <td className="muted">
                    {u.last_active ? new Date(u.last_active).toLocaleDateString() : "never"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
