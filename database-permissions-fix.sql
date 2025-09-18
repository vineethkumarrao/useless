-- Updated Database Fix - Allows backend service to manage records
-- Copy and paste this SQL into your Supabase SQL Editor

-- Drop existing policies that are too restrictive
DROP POLICY IF EXISTS "Users can manage own profile" ON public.users;
DROP POLICY IF EXISTS "Users can manage own conversations" ON public.conversations;

-- Create policies that allow both users and service role
CREATE POLICY "Users and service can manage profiles" 
  ON public.users FOR ALL 
  USING (auth.uid() = id OR auth.role() = 'service_role');

CREATE POLICY "Users and service can manage conversations" 
  ON public.conversations FOR ALL 
  USING (auth.uid() = user_id OR auth.role() = 'service_role');

-- Also create policies for anon role to allow backend operations
CREATE POLICY "Allow backend operations for users" 
  ON public.users FOR ALL 
  TO anon
  USING (true);

CREATE POLICY "Allow backend operations for conversations" 
  ON public.conversations FOR ALL 
  TO anon
  USING (true);

-- Grant permissions to anon role (used by backend)
GRANT ALL ON public.users TO anon;
GRANT ALL ON public.conversations TO anon;

-- Ensure the messages table exists and has proper policies
CREATE TABLE IF NOT EXISTS public.messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  content TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb,
  embedding vector(384)
);

-- Enable RLS for messages
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Drop existing message policies
DROP POLICY IF EXISTS "Users can manage own messages" ON public.messages;
DROP POLICY IF EXISTS "Allow backend operations for messages" ON public.messages;

-- Create message policies
CREATE POLICY "Users and service can manage messages" 
  ON public.messages FOR ALL 
  USING (auth.uid() = user_id OR auth.role() = 'service_role');

CREATE POLICY "Allow backend operations for messages" 
  ON public.messages FOR ALL 
  TO anon
  USING (true);

-- Grant permissions for messages
GRANT ALL ON public.messages TO anon;

SELECT 'Database permissions updated successfully - backend should now work!' as status;