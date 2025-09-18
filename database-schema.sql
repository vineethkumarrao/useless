-- Supabase Database Schema for Useless Chatbot
-- This script sets up the complete database schema including authentication, vector storage, and integrations

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create custom types for better data organization
CREATE TYPE integration_type AS ENUM ('gmail', 'gdrive', 'gsheets', 'notion');
CREATE TYPE oauth_token_status AS ENUM ('active', 'expired', 'revoked');

-- Users table (extending Supabase auth.users)
-- This table stores additional user profile information
CREATE TABLE IF NOT EXISTS public.users (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_login TIMESTAMPTZ,
  is_premium BOOLEAN DEFAULT FALSE,
  preferences JSONB DEFAULT '{}'::jsonb
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Policy for users to only see their own data
CREATE POLICY "Users can view own profile" 
  ON public.users FOR SELECT 
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
  ON public.users FOR UPDATE 
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" 
  ON public.users FOR INSERT 
  WITH CHECK (auth.uid() = id);

-- OTP verification table for email verification during signup
CREATE TABLE IF NOT EXISTS public.otp_verifications (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  email TEXT NOT NULL,
  otp_code TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  is_verified BOOLEAN DEFAULT FALSE,
  attempts INT DEFAULT 0,
  max_attempts INT DEFAULT 3
);

-- Index for fast OTP lookups
CREATE INDEX IF NOT EXISTS idx_otp_email_code ON public.otp_verifications(email, otp_code);
CREATE INDEX IF NOT EXISTS idx_otp_expires ON public.otp_verifications(expires_at);

-- Conversations table to store chat history
CREATE TABLE IF NOT EXISTS public.conversations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL DEFAULT 'New Conversation',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  is_archived BOOLEAN DEFAULT FALSE,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable RLS for conversations
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own conversations" 
  ON public.conversations FOR ALL 
  USING (auth.uid() = user_id);

-- Messages table to store individual chat messages
CREATE TABLE IF NOT EXISTS public.messages (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  content TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb,
  -- Vector embedding for semantic search (384 dimensions for sentence-transformers/all-MiniLM-L6-v2)
  embedding vector(384)
);

-- Enable RLS for messages
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own messages" 
  ON public.messages FOR ALL 
  USING (auth.uid() = user_id);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON public.messages(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_user ON public.messages(user_id, created_at DESC);

-- Vector similarity search index (HNSW is better for large datasets)
CREATE INDEX IF NOT EXISTS idx_messages_embedding ON public.messages 
  USING hnsw (embedding vector_cosine_ops);

-- OAuth integrations table to store external app connections
CREATE TABLE IF NOT EXISTS public.oauth_integrations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  integration_type integration_type NOT NULL,
  provider_user_id TEXT,
  provider_email TEXT,
  access_token TEXT NOT NULL, -- This should be encrypted in the application layer
  refresh_token TEXT,
  token_expires_at TIMESTAMPTZ,
  scope TEXT[], -- Array of granted permissions
  status oauth_token_status DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_used TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}'::jsonb,
  UNIQUE(user_id, integration_type)
);

-- Enable RLS for oauth integrations
ALTER TABLE public.oauth_integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own integrations" 
  ON public.oauth_integrations FOR ALL 
  USING (auth.uid() = user_id);

-- Integration usage logs for analytics and debugging
CREATE TABLE IF NOT EXISTS public.integration_logs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  integration_id UUID REFERENCES public.oauth_integrations(id) ON DELETE CASCADE NOT NULL,
  action TEXT NOT NULL, -- e.g., 'fetch_emails', 'create_document', etc.
  status TEXT NOT NULL CHECK (status IN ('success', 'error', 'pending')),
  request_data JSONB,
  response_data JSONB,
  error_message TEXT,
  execution_time_ms INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS for integration logs
ALTER TABLE public.integration_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own integration logs" 
  ON public.integration_logs FOR SELECT 
  USING (auth.uid() = user_id);

-- Rate limiting table to prevent abuse
CREATE TABLE IF NOT EXISTS public.rate_limits (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  ip_address INET,
  endpoint TEXT NOT NULL,
  request_count INT DEFAULT 1,
  window_start TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, endpoint, window_start)
);

-- Knowledge base table for storing embeddings of important information
CREATE TABLE IF NOT EXISTS public.knowledge_base (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source_type TEXT, -- 'manual', 'email', 'document', etc.
  source_id TEXT, -- ID from the source system
  tags TEXT[],
  embedding vector(384),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable RLS for knowledge base
ALTER TABLE public.knowledge_base ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own knowledge" 
  ON public.knowledge_base FOR ALL 
  USING (auth.uid() = user_id OR user_id IS NULL); -- Allow global knowledge entries

-- Vector similarity search index for knowledge base
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON public.knowledge_base 
  USING hnsw (embedding vector_cosine_ops);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_knowledge_user ON public.knowledge_base(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON public.knowledge_base USING GIN(tags);

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at timestamps
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON public.conversations 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_oauth_integrations_updated_at BEFORE UPDATE ON public.oauth_integrations 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON public.knowledge_base 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to clean up expired OTP codes
CREATE OR REPLACE FUNCTION cleanup_expired_otps()
RETURNS void AS $$
BEGIN
    DELETE FROM public.otp_verifications 
    WHERE expires_at < NOW() - INTERVAL '1 day';
END;
$$ language 'plpgsql';

-- Function to perform vector similarity search on messages
CREATE OR REPLACE FUNCTION search_similar_messages(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.8,
  match_count int DEFAULT 5,
  target_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  conversation_id uuid,
  content text,
  role text,
  created_at timestamptz,
  similarity float
) 
language sql stable
as $$
  SELECT 
    m.id,
    m.conversation_id,
    m.content,
    m.role,
    m.created_at,
    1 - (m.embedding <=> query_embedding) as similarity
  FROM public.messages m
  WHERE 
    (target_user_id IS NULL OR m.user_id = target_user_id)
    AND m.embedding IS NOT NULL
    AND 1 - (m.embedding <=> query_embedding) > match_threshold
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Function to search knowledge base
CREATE OR REPLACE FUNCTION search_knowledge_base(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.8,
  match_count int DEFAULT 5,
  target_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  title text,
  content text,
  source_type text,
  tags text[],
  created_at timestamptz,
  similarity float
) 
language sql stable
as $$
  SELECT 
    kb.id,
    kb.title,
    kb.content,
    kb.source_type,
    kb.tags,
    kb.created_at,
    1 - (kb.embedding <=> query_embedding) as similarity
  FROM public.knowledge_base kb
  WHERE 
    (target_user_id IS NULL OR kb.user_id = target_user_id OR kb.user_id IS NULL)
    AND kb.embedding IS NOT NULL
    AND 1 - (kb.embedding <=> query_embedding) > match_threshold
  ORDER BY kb.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Create a scheduled function to clean up old data (can be called via pg_cron if available)
CREATE OR REPLACE FUNCTION maintenance_cleanup()
RETURNS void AS $$
BEGIN
    -- Clean up expired OTPs
    PERFORM cleanup_expired_otps();
    
    -- Clean up old rate limiting records (older than 24 hours)
    DELETE FROM public.rate_limits 
    WHERE created_at < NOW() - INTERVAL '24 hours';
    
    -- Clean up old integration logs (older than 30 days)
    DELETE FROM public.integration_logs 
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ language 'plpgsql';

-- Insert some default knowledge base entries (optional)
INSERT INTO public.knowledge_base (title, content, source_type, tags) VALUES
('Chatbot Capabilities', 'This AI chatbot can help with research, analysis, writing tasks, and integrations with Gmail, Google Drive, Google Sheets, and Notion.', 'manual', ARRAY['features', 'capabilities']),
('Getting Started', 'To get started, sign up for an account and connect your external services through the integrations panel.', 'manual', ARRAY['onboarding', 'guide'])
ON CONFLICT DO NOTHING;

-- Grant necessary permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- Comments for documentation
COMMENT ON TABLE public.users IS 'Extended user profiles with additional information beyond Supabase auth';
COMMENT ON TABLE public.conversations IS 'Chat conversation containers for organizing messages';
COMMENT ON TABLE public.messages IS 'Individual chat messages with vector embeddings for semantic search';
COMMENT ON TABLE public.oauth_integrations IS 'OAuth token storage for external service integrations';
COMMENT ON TABLE public.knowledge_base IS 'Vector storage for searchable knowledge and context';
COMMENT ON COLUMN public.messages.embedding IS 'Vector embedding for semantic similarity search (384 dimensions)';
COMMENT ON FUNCTION search_similar_messages IS 'Vector similarity search for finding related conversation history';
COMMENT ON FUNCTION search_knowledge_base IS 'Vector similarity search for knowledge base entries';