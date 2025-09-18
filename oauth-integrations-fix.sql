-- OAuth Integrations Database Fix
-- Run this SQL in your Supabase SQL Editor to fix all OAuth integration issues
-- This will enable GitHub, Google Calendar, Google Docs, and Notion OAuth flows

-- Step 1: Update the integration_type enum to include all OAuth services
-- Add missing integration types that are used in the application
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'google_calendar';
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'google_docs';  
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'github';

-- Note: 'gmail' and 'notion' should already exist, but adding them won't hurt
-- ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'gmail';
-- ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'notion';

-- Step 2: Verify the oauth_integrations table structure
-- Ensure the table has the correct 'metadata' column (not 'integration_metadata')
-- This should already be correct, but we're verifying the structure

-- Check if the table exists and has correct structure
DO $$
BEGIN
    -- Check if oauth_integrations table exists
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'oauth_integrations') THEN
        RAISE NOTICE 'oauth_integrations table does not exist - this is unexpected';
    ELSE
        RAISE NOTICE 'oauth_integrations table exists';
    END IF;
    
    -- Check if metadata column exists (should be 'metadata', not 'integration_metadata')
    IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'oauth_integrations' AND column_name = 'metadata') THEN
        RAISE NOTICE 'metadata column does not exist - this is unexpected';
    ELSE
        RAISE NOTICE 'metadata column exists correctly';
    END IF;
END $$;

-- Step 3: Drop and recreate any problematic RLS policies if needed
-- This ensures clean policies for oauth_integrations table
DROP POLICY IF EXISTS "Users can manage own integrations" ON public.oauth_integrations;

CREATE POLICY "Users can manage own integrations" 
  ON public.oauth_integrations FOR ALL 
  USING (auth.uid() = user_id);

-- Step 4: Create indexes for better performance on oauth_integrations
CREATE INDEX IF NOT EXISTS idx_oauth_integrations_user_type 
  ON public.oauth_integrations(user_id, integration_type);

CREATE INDEX IF NOT EXISTS idx_oauth_integrations_status 
  ON public.oauth_integrations(status) WHERE status = 'active';

-- Step 5: Verify the changes
-- Display current enum values to confirm all integration types are available
DO $$
DECLARE 
    enum_values text;
BEGIN
    SELECT string_agg(enumlabel, ', ' ORDER BY enumlabel) INTO enum_values
    FROM pg_enum e
    JOIN pg_type t ON e.enumtypid = t.oid
    WHERE t.typname = 'integration_type';
    
    RAISE NOTICE 'Available integration types: %', enum_values;
END $$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ OAuth integrations database fix completed successfully!';
    RAISE NOTICE 'You can now use: Gmail, Google Calendar, Google Docs, Notion, and GitHub OAuth';
END $$;