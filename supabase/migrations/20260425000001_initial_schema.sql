-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Runs table
CREATE TABLE runs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  objective   TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'CREATED'
    CHECK (status IN ('CREATED','RUNNING','PAUSED','COMPLETED','FAILED','CANCELLED')),
  total_tokens INT DEFAULT 0,
  cost_usd    DECIMAL(10,6) DEFAULT 0,
  result      TEXT,
  error       TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Run events table
CREATE TABLE run_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id      UUID REFERENCES runs(id) ON DELETE CASCADE,
  type        TEXT NOT NULL
    CHECK (type IN (
      'agent_started','skill_called','skill_result',
      'hitl_required','hitl_resolved',
      'budget_warning','run_completed','run_failed','run_cancelled'
    )),
  agent_name  TEXT,
  payload     JSONB,
  tokens_used INT DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Memories table (pgvector RAG)
CREATE TABLE memories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  run_id      UUID REFERENCES runs(id) ON DELETE SET NULL,
  content     TEXT NOT NULL,
  embedding   vector(768),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX memories_embedding_idx ON memories
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- updated_at trigger for runs
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER runs_updated_at
  BEFORE UPDATE ON runs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE run_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own runs" ON runs
  FOR ALL USING (user_id = auth.uid());

CREATE POLICY "users own run_events via runs" ON run_events
  FOR ALL USING (
    run_id IN (SELECT id FROM runs WHERE user_id = auth.uid())
  );

CREATE POLICY "users own memories" ON memories
  FOR ALL USING (user_id = auth.uid());
