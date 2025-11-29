-- Migration: Add metadata column to conversations table
-- Purpose: Store conversation state like order_draft between chat calls
-- This allows the agent to maintain context across multiple messages

-- Add metadata column to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Add index for efficient querying of metadata
CREATE INDEX IF NOT EXISTS idx_conversations_metadata ON conversations USING GIN (metadata);

-- Comment explaining the column
COMMENT ON COLUMN conversations.metadata IS 'Stores conversation state including order_draft, last_intent, and other contextual data';
