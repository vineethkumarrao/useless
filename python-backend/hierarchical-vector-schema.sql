-- Hierarchical Vector Storage Schema for Conversation Memory
-- This creates a proper multi-level vector storage system

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. USER MEMORY TABLE - Cross-conversation user context and preferences
CREATE TABLE IF NOT EXISTS public.user_memory_vectors (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL,
  memory_type TEXT NOT NULL CHECK (memory_type IN ('preference', 'fact', 'context')),
  content TEXT NOT NULL,
  source_conversation_id TEXT, -- Which conversation this memory came from
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  importance_score FLOAT DEFAULT 0.5, -- 0.0 to 1.0, higher = more important
  access_count INTEGER DEFAULT 0, -- How often this memory is accessed
  -- Vector embedding for semantic search (384 dimensions for BGE-small-en-v1.5)
  embedding vector(384)
);

-- 2. CONVERSATION MEMORY TABLE - Individual conversation context
CREATE TABLE IF NOT EXISTS public.conversation_memory_vectors (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL,
  conversation_id TEXT NOT NULL,
  message_id UUID, -- Link to specific message if applicable
  content TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  turn_number INTEGER, -- Order within conversation
  created_at TIMESTAMPTZ DEFAULT NOW(),
  -- Vector embedding for semantic search
  embedding vector(384)
);

-- 3. CONVERSATION METADATA TABLE - Track conversation summaries and context
CREATE TABLE IF NOT EXISTS public.conversation_summaries (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL,
  conversation_id TEXT NOT NULL UNIQUE,
  title TEXT,
  summary TEXT, -- AI-generated summary of the conversation
  key_topics TEXT[], -- Array of key topics discussed
  message_count INTEGER DEFAULT 0,
  start_time TIMESTAMPTZ DEFAULT NOW(),
  last_activity TIMESTAMPTZ DEFAULT NOW(),
  -- Summary embedding for conversation-level search
  summary_embedding vector(384)
);

-- Enable RLS for all tables
ALTER TABLE public.user_memory_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_memory_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_summaries ENABLE ROW LEVEL SECURITY;

-- Policies for user_memory_vectors
CREATE POLICY "Users can manage own user memory" 
  ON public.user_memory_vectors FOR ALL 
  USING (true); -- Adjust this for proper user isolation in production

-- Policies for conversation_memory_vectors  
CREATE POLICY "Users can manage own conversation memory" 
  ON public.conversation_memory_vectors FOR ALL 
  USING (true); -- Adjust this for proper user isolation in production

-- Policies for conversation_summaries
CREATE POLICY "Users can manage own conversation summaries" 
  ON public.conversation_summaries FOR ALL 
  USING (true); -- Adjust this for proper user isolation in production

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_memory_user_type ON public.user_memory_vectors(user_id, memory_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_memory_user_conv ON public.conversation_memory_vectors(user_id, conversation_id, turn_number);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_user ON public.conversation_summaries(user_id, last_activity DESC);

-- Vector indexes for similarity search
CREATE INDEX IF NOT EXISTS idx_user_memory_embedding ON public.user_memory_vectors 
  USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_conversation_memory_embedding ON public.conversation_memory_vectors 
  USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_conversation_summary_embedding ON public.conversation_summaries 
  USING hnsw (summary_embedding vector_cosine_ops);

-- FUNCTIONS FOR MEMORY OPERATIONS

-- 1. Search user memory across all conversations
CREATE OR REPLACE FUNCTION search_user_memory(
  query_embedding vector(384),
  target_user_id uuid,
  memory_types text[] DEFAULT ARRAY['preference', 'fact', 'context'],
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10
)
RETURNS setof user_memory_vectors
LANGUAGE sql
AS $$
  SELECT *
  FROM user_memory_vectors
  WHERE user_memory_vectors.user_id = target_user_id
    AND memory_type = ANY(memory_types)
    AND user_memory_vectors.embedding <=> query_embedding < 1 - match_threshold
  ORDER BY user_memory_vectors.embedding <=> query_embedding ASC
  LIMIT least(match_count, 50);
$$;

-- 2. Search conversation memory within a specific conversation
CREATE OR REPLACE FUNCTION search_conversation_memory(
  query_embedding vector(384),
  target_user_id uuid,
  target_conversation_id text,
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10
)
RETURNS setof conversation_memory_vectors
LANGUAGE sql
AS $$
  SELECT *
  FROM conversation_memory_vectors
  WHERE conversation_memory_vectors.user_id = target_user_id
    AND conversation_memory_vectors.conversation_id = target_conversation_id
    AND conversation_memory_vectors.embedding <=> query_embedding < 1 - match_threshold
  ORDER BY conversation_memory_vectors.embedding <=> query_embedding ASC
  LIMIT least(match_count, 20);
$$;

-- 3. Search conversation summaries to find relevant past conversations
CREATE OR REPLACE FUNCTION search_conversation_summaries(
  query_embedding vector(384),
  target_user_id uuid,
  match_threshold float DEFAULT 0.6,
  match_count int DEFAULT 5
)
RETURNS setof conversation_summaries
LANGUAGE sql
AS $$
  SELECT *
  FROM conversation_summaries
  WHERE conversation_summaries.user_id = target_user_id
    AND conversation_summaries.summary_embedding <=> query_embedding < 1 - match_threshold
  ORDER BY conversation_summaries.summary_embedding <=> query_embedding ASC
  LIMIT least(match_count, 10);
$$;

-- 4. Function to update memory importance and access count
CREATE OR REPLACE FUNCTION update_memory_access(memory_id uuid)
RETURNS void
LANGUAGE sql
AS $$
  UPDATE user_memory_vectors 
  SET 
    access_count = access_count + 1,
    updated_at = NOW(),
    importance_score = LEAST(1.0, importance_score + 0.1)
  WHERE id = memory_id;
$$;

-- Success message
SELECT 'Hierarchical vector memory system setup completed successfully!' as status;