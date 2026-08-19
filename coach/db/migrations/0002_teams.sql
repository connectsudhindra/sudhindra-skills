-- Adds a team dimension: users optionally belong to a team, so the
-- dashboard can show team-level trends and cross-team comparison, not just
-- one flat roster.
CREATE TABLE IF NOT EXISTS teams (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id);
CREATE INDEX IF NOT EXISTS idx_users_team ON users (team_id);

INSERT INTO schema_migrations (version) VALUES ('0002_teams') ON CONFLICT DO NOTHING;
