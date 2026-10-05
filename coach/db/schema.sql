-- GCCF prompt-coaching schema.
-- Applied automatically on first Postgres boot via docker-entrypoint-initdb.d;
-- for an already-running database, use coach/db/migrate.py + coach/db/migrations/*.sql instead.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE levels (
  level_num      SMALLINT PRIMARY KEY,
  name           TEXT NOT NULL UNIQUE,
  min_score      NUMERIC(5,2) NOT NULL,
  description    TEXT,
  next_level_tip TEXT
);

CREATE TABLE teams (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT NOT NULL,
  email          TEXT NOT NULL UNIQUE,
  team_id        UUID REFERENCES teams(id),
  current_level  SMALLINT NOT NULL REFERENCES levels(level_num) DEFAULT 1,
  coaching_mode  TEXT NOT NULL DEFAULT 'end_of_session'
                   CHECK (coaching_mode IN ('in_session', 'end_of_session', 'off')),
  is_admin       BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_team ON users (team_id);

CREATE TABLE sessions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id),
  claude_session_id TEXT NOT NULL,
  started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at          TIMESTAMPTZ,
  session_level     SMALLINT REFERENCES levels(level_num),
  UNIQUE (user_id, claude_session_id)
);
CREATE INDEX idx_sessions_open ON sessions (user_id) WHERE ended_at IS NULL;

CREATE TABLE prompts (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id          UUID NOT NULL REFERENCES sessions(id),
  user_id             UUID NOT NULL REFERENCES users(id),
  prompt_text         TEXT NOT NULL,
  is_scorable         BOOLEAN NOT NULL DEFAULT true,
  level_at_submission SMALLINT REFERENCES levels(level_num),
  submitted_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_prompts_user_time ON prompts (user_id, submitted_at DESC);
CREATE INDEX idx_prompts_session ON prompts (session_id);

-- One row per (prompt, scoring method) so heuristic and LLM scores coexist for
-- direct comparison instead of forcing a single method's result to win.
CREATE TABLE prompt_scores (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_id         UUID NOT NULL REFERENCES prompts(id),
  scoring_method    TEXT NOT NULL CHECK (scoring_method IN ('heuristic', 'llm')),
  model_name        TEXT,
  goal_score        NUMERIC(5,2) NOT NULL CHECK (goal_score BETWEEN 0 AND 100),
  context_score     NUMERIC(5,2) NOT NULL CHECK (context_score BETWEEN 0 AND 100),
  constraints_score NUMERIC(5,2) NOT NULL CHECK (constraints_score BETWEEN 0 AND 100),
  format_score      NUMERIC(5,2) NOT NULL CHECK (format_score BETWEEN 0 AND 100),
  composite_score   NUMERIC(5,2) GENERATED ALWAYS AS
                       ((goal_score + context_score + constraints_score + format_score) / 4) STORED,
  rationale         TEXT,
  dimension_feedback JSONB,
  latency_ms        INTEGER,
  scored_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (prompt_id, scoring_method)
);
CREATE INDEX idx_prompt_scores_prompt ON prompt_scores (prompt_id);

CREATE TABLE level_history (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id),
  level_num   SMALLINT NOT NULL REFERENCES levels(level_num),
  achieved_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_level_history_user ON level_history (user_id, achieved_at DESC);

CREATE TABLE coaching_feedback (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_id     UUID REFERENCES prompts(id),
  session_id    UUID REFERENCES sessions(id),
  user_id       UUID NOT NULL REFERENCES users(id),
  feedback_type TEXT NOT NULL CHECK (feedback_type IN ('in_session', 'end_of_session')),
  feedback_text TEXT NOT NULL,
  blocked       BOOLEAN NOT NULL DEFAULT false,
  delivered_at  TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_coaching_feedback_user ON coaching_feedback (user_id, created_at DESC);
CREATE INDEX idx_coaching_feedback_undelivered ON coaching_feedback (user_id) WHERE delivered_at IS NULL;

CREATE TABLE schema_migrations (
  version    TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
