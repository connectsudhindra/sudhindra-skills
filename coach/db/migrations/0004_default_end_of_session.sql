-- New users default to end_of_session: blocking on a fresh install erased
-- reasonable short asks ("check all skills") because the heuristic scorer
-- expects code-shaped prompts. Blocking stays available as an opt-in via
-- levelset. Existing rows keep whatever mode they already have.
ALTER TABLE users ALTER COLUMN coaching_mode SET DEFAULT 'end_of_session';

INSERT INTO schema_migrations (version) VALUES ('0004_default_end_of_session') ON CONFLICT DO NOTHING;
