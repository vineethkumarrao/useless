-- Chat History Vectors Setup for Backend Compatibility
-- This creates the exact table and function names expected by the backend

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create chat_history_vectors table (backend expects this exact name)
CREATE TABLE IF NOT EXISTS public.chat_history_vectors (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL,
  conversation_id TEXT NOT NULL DEFAULT 'default',
  message TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  -- Vector embedding for semantic search (384 dimensions for sentence-transformers/all-MiniLM-L6-v2)
  embedding vector(384)
);

-- Enable RLS for chat_history_vectors  
ALTER TABLE public.chat_history_vectors ENABLE ROW LEVEL SECURITY;

-- Create policy to allow users to manage their own chat history
CREATE POLICY "Users can manage own chat history" 
  ON public.chat_history_vectors FOR ALL 
  USING (true); -- For now, allow all operations (you can restrict this later)

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_chat_history_user_conversation ON public.chat_history_vectors(user_id, conversation_id, created_at DESC);

-- Vector similarity search index (HNSW is better for large datasets)
CREATE INDEX IF NOT EXISTS idx_chat_history_embedding ON public.chat_history_vectors 
  USING hnsw (embedding vector_cosine_ops);

-- Function to match chat history based on semantic similarity (backend expects this exact name)
CREATE OR REPLACE FUNCTION match_chat_history(
  conversation_id text,
  match_count int,
  match_threshold float,
  query_embedding vector(384),
  user_id uuid
)
RETURNS setof chat_history_vectors
LANGUAGE sql
AS $$
  SELECT *
  FROM chat_history_vectors
  WHERE chat_history_vectors.user_id = user_id
    AND chat_history_vectors.conversation_id = conversation_id
    AND chat_history_vectors.embedding <=> query_embedding < 1 - match_threshold
  ORDER BY chat_history_vectors.embedding <=> query_embedding ASC
  LIMIT least(match_count, 200);
$$;

-- Success message
SELECT 'Chat history vectors setup completed successfully!' as status;