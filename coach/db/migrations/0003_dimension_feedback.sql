-- Structured per-dimension feedback (status, issue codes, message, one
-- actionable tip) alongside the numeric scores -- this is what turns a bare
-- score into actual coaching. Nullable: only the heuristic scorer populates
-- it today (see coach/api/scoring/heuristic.py); LLM rows may stay NULL.
ALTER TABLE prompt_scores ADD COLUMN IF NOT EXISTS dimension_feedback JSONB;

INSERT INTO schema_migrations (version) VALUES ('0003_dimension_feedback') ON CONFLICT DO NOTHING;
