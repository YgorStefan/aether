ALTER TABLE run_events DROP CONSTRAINT IF EXISTS run_events_type_check;

ALTER TABLE run_events ADD CONSTRAINT run_events_type_check CHECK (type IN (
  'agent_started',
  'task_started',
  'task_completed',
  'skill_called',
  'skill_result',
  'hitl_required',
  'hitl_resolved',
  'budget_warning',
  'budget_exceeded',
  'run_completed',
  'run_failed',
  'run_cancelled'
));
