-- Supabase Cloud provisiona automaticamente estes grants para todo projeto novo,
-- garantindo que anon/authenticated/service_role consigam operar via PostgREST
-- (a autorização real de linhas continua sendo feita pelas RLS policies; service_role
-- tem BYPASSRLS e por isso precisa dos grants de tabela para funcionar como esperado
-- no backend). Ao rodar localmente via `supabase start`, esses grants não vêm
-- pré-configurados, então sem esta migration nenhuma tabela é acessível via PostgREST
-- — nem mesmo pela service role usada pelo backend.
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO anon, authenticated, service_role;
