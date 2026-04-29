-- Execute no SQL Editor do Supabase (Dashboard → SQL Editor → New query)
-- Cria função para busca por similaridade cosine com filtro por usuário e threshold

CREATE OR REPLACE FUNCTION match_memories(
  query_embedding vector(768),
  match_user_id uuid,
  match_threshold float,
  match_count int
)
RETURNS TABLE (id uuid, content text, similarity float)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    memories.id,
    memories.content,
    1 - (memories.embedding <=> query_embedding) AS similarity
  FROM memories
  WHERE memories.user_id = match_user_id
    AND 1 - (memories.embedding <=> query_embedding) > match_threshold
  ORDER BY memories.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
