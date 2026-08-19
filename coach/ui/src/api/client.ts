import type {
  CoachingFeedback,
  LevelDistributionEntry,
  Prompt,
  ScoringComparison,
  Team,
  Trend,
  UserDetail,
  UserSummary,
} from "../types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8787";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`${path} -> ${response.status}`);
  }
  return (await response.json()) as T;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v != null);
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join("&");
}

export const api = {
  listUsers: (level?: number, teamId?: string) =>
    getJson<UserSummary[]>(`/users${buildQuery({ level, team_id: teamId })}`),

  getUserByEmail: (email: string) =>
    getJson<UserSummary>(`/users/by-email/${encodeURIComponent(email)}`),

  getUserDetail: (userId: string) => getJson<UserDetail>(`/users/${userId}`),

  getUserPrompts: (userId: string, limit = 50, offset = 0) =>
    getJson<Prompt[]>(`/users/${userId}/prompts?limit=${limit}&offset=${offset}`),

  getUserFeedback: (userId: string) => getJson<CoachingFeedback[]>(`/users/${userId}/feedback`),

  levelDistribution: () => getJson<LevelDistributionEntry[]>("/dashboard/level-distribution"),

  scoringComparison: () => getJson<ScoringComparison>("/dashboard/scoring-comparison"),

  listTeams: () => getJson<Team[]>("/teams"),

  trend: (teamId?: string, days = 30) => getJson<Trend>(`/dashboard/trend${buildQuery({ team_id: teamId, days })}`),
};
