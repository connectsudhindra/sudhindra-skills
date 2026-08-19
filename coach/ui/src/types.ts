export type CoachingMode = "in_session" | "end_of_session" | "off";
export type ScoringMethod = "heuristic" | "llm";

export interface GCCFScore {
  goal: number;
  context: number;
  constraints: number;
  format: number;
  rationale?: string | null;
}

export interface UserSummary {
  id: string;
  name: string;
  email: string;
  team_id: string | null;
  team_name: string | null;
  current_level: number;
  current_level_name: string;
  coaching_mode: CoachingMode;
  rolling_composite: number | null;
  scorable_prompt_count: number;
  last_active: string | null;
}

export interface Team {
  id: string;
  name: string;
  member_count: number;
  avg_level: number | null;
  avg_composite: number | null;
}

export interface TrendPoint {
  day: string;
  avg_composite: number;
  avg_goal: number;
  avg_context: number;
  avg_constraints: number;
  avg_format: number;
  prompt_count: number;
}

export interface Trend {
  scope: string;
  points: TrendPoint[];
}

export interface LevelHistoryEntry {
  level_num: number;
  achieved_at: string;
}

export interface UserDetail {
  user: UserSummary;
  level_history: LevelHistoryEntry[];
  gccf_averages: GCCFScore | null;
}

export type DimensionStatus = "strong" | "developing" | "weak";
export type DimensionKey = "goal" | "context" | "constraints" | "format";

export interface IssueDetail {
  code: string;
  weight: number;
  message: string;
  tip: string;
}

export interface DimensionFeedback {
  score: number;
  status: DimensionStatus;
  issues: string[];
  message: string;
  tip: string | null;
  issue_detail: IssueDetail[];
}

export interface PromptScore {
  scoring_method: ScoringMethod;
  goal_score: number;
  context_score: number;
  constraints_score: number;
  format_score: number;
  composite_score: number;
  rationale: string | null;
  dimension_feedback: Record<DimensionKey, DimensionFeedback> | null;
  latency_ms: number | null;
}

export interface Prompt {
  id: string;
  prompt_text: string;
  is_scorable: boolean;
  submitted_at: string;
  scores: PromptScore[];
}

export interface CoachingFeedback {
  id: string;
  feedback_type: "in_session" | "end_of_session";
  feedback_text: string;
  blocked: boolean;
  delivered_at: string | null;
  created_at: string;
}

export interface LevelDistributionEntry {
  level_num: number;
  name: string;
  user_count: number;
}

export interface ScoringComparison {
  sample_size: number;
  mean_abs_diff: number | null;
  pairs: { heuristic_composite: number; llm_composite: number }[];
}

export const LEVEL_NAMES = ["", "Operator", "Composer", "Delegator", "Orchestrator", "Architect"];

export type Direction = "improving" | "flat" | "declining";

export interface DimensionProgress {
  dimension: DimensionKey;
  recent_avg: number | null;
  prior_avg: number | null;
  delta: number | null;
  direction: Direction;
  sample_size: number;
  most_common_issue: string | null;
  most_common_issue_message: string | null;
  tip: string | null;
}

export interface Progress {
  scope: string;
  scope_label: string;
  dimensions: DimensionProgress[];
  strongest_dimension: DimensionKey | null;
  weakest_dimension: DimensionKey | null;
  headline: string;
}

export interface SessionSummary {
  id: string;
  claude_session_id: string;
  started_at: string;
  ended_at: string | null;
  session_level: number | null;
  session_level_name: string | null;
  prompt_count: number;
  avg_composite: number | null;
}

export interface SessionDetail {
  session: SessionSummary;
  prompts: Prompt[];
}
