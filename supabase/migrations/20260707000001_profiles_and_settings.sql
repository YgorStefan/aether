-- Profiles: espelha auth.users com role para controle de acesso (admin/user)
CREATE TABLE profiles (
  user_id     UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email       TEXT NOT NULL,
  role        TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users read own profile" ON profiles
  FOR SELECT USING (user_id = auth.uid());

-- Popula profiles automaticamente a cada novo usuário cadastrado
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (user_id, email) VALUES (NEW.id, NEW.email);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Backfill para usuários que já existiam antes desta migration
INSERT INTO profiles (user_id, email)
SELECT id, email FROM auth.users
ON CONFLICT (user_id) DO NOTHING;

-- Para promover um usuário a admin, rode manualmente:
--   UPDATE profiles SET role = 'admin' WHERE email = 'seu-email@exemplo.com';

-- Configurações de LLM por usuário (chave de API criptografada pelo backend)
CREATE TABLE user_settings (
  user_id     UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  provider    TEXT NOT NULL,
  api_key     TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
-- Sem policies: acesso apenas via service role do backend (deny-all para clientes).

CREATE TRIGGER user_settings_updated_at
  BEFORE UPDATE ON user_settings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Bucket de storage usado pela skill file_writer.
-- Público para leitura (get_public_url); escrita só pelo backend via service role,
-- que ignora RLS — por isso não é necessária nenhuma policy em storage.objects.
INSERT INTO storage.buckets (id, name, public)
VALUES ('artifacts', 'artifacts', true)
ON CONFLICT (id) DO NOTHING;
