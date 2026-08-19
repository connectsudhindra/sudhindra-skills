INSERT INTO levels (level_num, name, min_score, description, next_level_tip) VALUES
(1, 'Operator', 0.00,
 'Uses prompts inconsistently; burns tokens and turns re-explaining goals that were never stated.',
 'Name the goal before you type -- one sentence stating what "done" looks like turns a guess into a request.'),
(2, 'Composer', 45.00,
 'Gets work done in a smarter, more efficient way -- prompts carry real context and a shape for the answer.',
 'Attach the context Claude cannot infer -- the file, the error, the constraint you already know matters -- and stop re-explaining it every turn.'),
(3, 'Delegator', 65.00,
 'Knows how to delegate tasks to agents and skills with the right scope instead of driving every step by hand.',
 'You have the four dimensions covered solo. Now hand a scoped, self-contained task to an agent or skill instead of running it yourself.'),
(4, 'Orchestrator', 80.00,
 'Achieves multi-agent coordination; splits larger problems across delegates and supervises the result.',
 'Stop running one delegate at a time -- split the problem and run several agents in parallel, each with a narrow mandate.'),
(5, 'Architect', 92.00,
 'Expert at getting things done in a fully autonomous way; prompts read like specs, not requests.',
 'You are already doing this well. The next gain is systemic: teach the pattern back into the team''s own skills and hooks.')
ON CONFLICT (level_num) DO NOTHING;
