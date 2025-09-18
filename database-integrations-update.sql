-- Database Schema Update for New Integrations
-- This script adds support for Google Calendar, Google Docs, Notion, and GitHub integrations
-- Run this after the main database-schema.sql has been executed

-- Update the integration_type enum to include new integrations
-- Note: In PostgreSQL, you can add new values to an enum using ALTER TYPE
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'google_calendar';
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'google_docs';
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'github';

-- Create a new table for storing app-specific data with vector embeddings
-- This will store all data fetched from integrated apps for AI processing
CREATE TABLE IF NOT EXISTS public.integration_data (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  integration_id UUID REFERENCES public.oauth_integrations(id) ON DELETE CASCADE NOT NULL,
  integration_type integration_type NOT NULL,
  
  -- Data identification and metadata
  external_id TEXT NOT NULL, -- ID from the external service (e.g., email ID, calendar event ID, etc.)
  data_type TEXT NOT NULL, -- 'email', 'calendar_event', 'document', 'repository', 'issue', 'page', etc.
  title TEXT NOT NULL,
  content TEXT, -- Full content/body
  summary TEXT, -- AI-generated summary for quick access
  
  -- Timestamps and status
  external_created_at TIMESTAMPTZ, -- When the item was created in the external service
  external_updated_at TIMESTAMPTZ, -- When the item was last updated in the external service
  last_synced_at TIMESTAMPTZ DEFAULT NOW(),
  sync_status TEXT DEFAULT 'synced' CHECK (sync_status IN ('synced', 'pending', 'error', 'deleted')),
  
  -- Vector embedding for semantic search (384 dimensions for sentence-transformers/all-MiniLM-L6-v2)
  embedding vector(384),
  
  -- Structured metadata from the source
  metadata JSONB DEFAULT '{}'::jsonb,
  
  -- Additional properties
  tags TEXT[],
  is_important BOOLEAN DEFAULT FALSE,
  is_archived BOOLEAN DEFAULT FALSE,
  
  -- Standard timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Ensure we don't duplicate data from the same source
  UNIQUE(integration_id, external_id, data_type)
);

-- Enable RLS for integration data
ALTER TABLE public.integration_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own integration data" 
  ON public.integration_data FOR ALL 
  USING (auth.uid() = user_id);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_integration_data_user ON public.integration_data(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_integration_data_integration ON public.integration_data(integration_id, data_type);
CREATE INDEX IF NOT EXISTS idx_integration_data_external ON public.integration_data(external_id, data_type);
CREATE INDEX IF NOT EXISTS idx_integration_data_type ON public.integration_data(integration_type, data_type);
CREATE INDEX IF NOT EXISTS idx_integration_data_sync ON public.integration_data(sync_status, last_synced_at);
CREATE INDEX IF NOT EXISTS idx_integration_data_tags ON public.integration_data USING GIN(tags);

-- Vector similarity search index for integration data
CREATE INDEX IF NOT EXISTS idx_integration_data_embedding ON public.integration_data 
  USING hnsw (embedding vector_cosine_ops);

-- Function to search integration data by semantic similarity
CREATE OR REPLACE FUNCTION search_integration_data(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.8,
  match_count int DEFAULT 10,
  target_user_id uuid DEFAULT NULL,
  filter_integration_type integration_type DEFAULT NULL,
  filter_data_type text DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  integration_type integration_type,
  data_type text,
  title text,
  content text,
  summary text,
  external_created_at timestamptz,
  tags text[],
  metadata jsonb,
  similarity float
) 
language sql stable
as $$
  SELECT 
    id.id,
    id.integration_type,
    id.data_type,
    id.title,
    id.content,
    id.summary,
    id.external_created_at,
    id.tags,
    id.metadata,
    1 - (id.embedding <=> query_embedding) as similarity
  FROM public.integration_data id
  WHERE 
    (target_user_id IS NULL OR id.user_id = target_user_id)
    AND (filter_integration_type IS NULL OR id.integration_type = filter_integration_type)
    AND (filter_data_type IS NULL OR id.data_type = filter_data_type)
    AND id.embedding IS NOT NULL
    AND id.sync_status = 'synced'
    AND id.is_archived = FALSE
    AND 1 - (id.embedding <=> query_embedding) > match_threshold
  ORDER BY id.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Table for tracking sync jobs and their status
CREATE TABLE IF NOT EXISTS public.sync_jobs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  integration_id UUID REFERENCES public.oauth_integrations(id) ON DELETE CASCADE NOT NULL,
  integration_type integration_type NOT NULL,
  
  -- Job details
  job_type TEXT NOT NULL, -- 'full_sync', 'incremental_sync', 'manual_sync'
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  
  -- Progress tracking
  total_items INT DEFAULT 0,
  processed_items INT DEFAULT 0,
  new_items INT DEFAULT 0,
  updated_items INT DEFAULT 0,
  deleted_items INT DEFAULT 0,
  error_count INT DEFAULT 0,
  
  -- Timestamps
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  
  -- Error handling
  error_message TEXT,
  error_details JSONB,
  
  -- Metadata
  sync_params JSONB DEFAULT '{}'::jsonb, -- Parameters used for this sync
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS for sync jobs
ALTER TABLE public.sync_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sync jobs" 
  ON public.sync_jobs FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "System can manage sync jobs" 
  ON public.sync_jobs FOR ALL 
  USING (true); -- This will be restricted by application logic

-- Indexes for sync jobs
CREATE INDEX IF NOT EXISTS idx_sync_jobs_user ON public.sync_jobs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_integration ON public.sync_jobs(integration_id, status);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_status ON public.sync_jobs(status, started_at);

-- Table for storing webhook endpoints and their configurations
CREATE TABLE IF NOT EXISTS public.webhook_configurations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  integration_id UUID REFERENCES public.oauth_integrations(id) ON DELETE CASCADE NOT NULL,
  integration_type integration_type NOT NULL,
  
  -- Webhook details
  webhook_url TEXT NOT NULL,
  webhook_secret TEXT NOT NULL, -- For verifying webhook signatures
  webhook_events TEXT[] NOT NULL, -- Array of events to listen for
  
  -- Status and configuration
  is_active BOOLEAN DEFAULT TRUE,
  verification_token TEXT,
  is_verified BOOLEAN DEFAULT FALSE,
  
  -- External webhook ID (from the service provider)
  external_webhook_id TEXT,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_webhook_received TIMESTAMPTZ,
  
  -- Metadata
  configuration JSONB DEFAULT '{}'::jsonb,
  
  UNIQUE(integration_id, webhook_url)
);

-- Enable RLS for webhook configurations
ALTER TABLE public.webhook_configurations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own webhook configurations" 
  ON public.webhook_configurations FOR ALL 
  USING (auth.uid() = user_id);

-- Add trigger for integration_data updated_at
CREATE TRIGGER update_integration_data_updated_at BEFORE UPDATE ON public.integration_data 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add trigger for webhook_configurations updated_at
CREATE TRIGGER update_webhook_configurations_updated_at BEFORE UPDATE ON public.webhook_configurations 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to clean up old integration data (optional, for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_integration_data(retention_days int DEFAULT 90)
RETURNS int AS $$
DECLARE
  deleted_count int;
BEGIN
  DELETE FROM public.integration_data 
  WHERE 
    sync_status = 'deleted' 
    AND updated_at < NOW() - INTERVAL '1 day' * retention_days;
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ language 'plpgsql';

-- Function to get user's integration statistics
CREATE OR REPLACE FUNCTION get_user_integration_stats(target_user_id uuid)
RETURNS TABLE (
  integration_type integration_type,
  data_type text,
  total_count bigint,
  last_sync timestamptz
) 
language sql stable
as $$
  SELECT 
    id.integration_type,
    id.data_type,
    COUNT(*) as total_count,
    MAX(id.last_synced_at) as last_sync
  FROM public.integration_data id
  WHERE 
    id.user_id = target_user_id
    AND id.sync_status = 'synced'
    AND id.is_archived = FALSE
  GROUP BY id.integration_type, id.data_type
  ORDER BY id.integration_type, id.data_type;
$$;

-- Create a view for easy access to connected integrations with their data counts
CREATE OR REPLACE VIEW user_integrations_summary AS
SELECT 
  oi.user_id,
  oi.integration_type,
  oi.provider_email,
  oi.status,
  oi.created_at as connected_at,
  oi.last_used,
  COALESCE(data_stats.total_items, 0) as total_synced_items,
  COALESCE(data_stats.last_sync, oi.updated_at) as last_sync
FROM public.oauth_integrations oi
LEFT JOIN (
  SELECT 
    integration_id,
    COUNT(*) as total_items,
    MAX(last_synced_at) as last_sync
  FROM public.integration_data 
  WHERE sync_status = 'synced' AND is_archived = FALSE
  GROUP BY integration_id
) data_stats ON oi.id = data_stats.integration_id
WHERE oi.status = 'active';

-- Grant necessary permissions (adjust based on your Supabase configuration)
-- These might need to be run separately or adjusted based on your RLS policies

COMMENT ON TABLE public.integration_data IS 'Stores all data from integrated applications with vector embeddings for AI processing';
COMMENT ON TABLE public.sync_jobs IS 'Tracks synchronization jobs for integration data';
COMMENT ON TABLE public.webhook_configurations IS 'Manages webhook endpoints for real-time integration updates';
COMMENT ON VIEW user_integrations_summary IS 'Provides a summary view of user integrations with data statistics';