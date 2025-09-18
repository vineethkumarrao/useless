-- Add missing integration types to the enum
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'google_calendar';
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'google_docs';  
ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'github';

-- Add integration_metadata column as an alias to metadata for backward compatibility
-- (We'll update the code to use the existing 'metadata' column instead)

-- Update any existing Notion integrations to have the proper integration_type
-- This is safe to run multiple times
UPDATE public.oauth_integrations 
SET integration_type = 'notion'::integration_type 
WHERE integration_type IS NULL 
  AND (access_token LIKE '%notion%' OR provider_email LIKE '%notion%');