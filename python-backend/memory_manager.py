"""
Hierarchical Vector Memory Manager
Handles user-level, conversation-level, and cross-conversation memory using Supabase vector storage.
"""

import os
import asyncio
import uuid
import hashlib
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def email_to_uuid(email: str) -> str:
    """Convert email to a deterministic UUID format."""
    # Create a deterministic UUID from email using namespace UUID
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
    return str(uuid.uuid5(namespace, email.lower().strip()))

class HierarchicalMemoryManager:
    """Manages hierarchical vector memory storage and retrieval."""
    
    def __init__(self):
        try:
            # Use SUPABASE_KEY since that's what we have in .env
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
            supabase_url = os.getenv("SUPABASE_URL")
            
            if not supabase_key:
                raise ValueError("Neither SUPABASE_SERVICE_KEY nor SUPABASE_KEY found in environment")
            if not supabase_url:
                raise ValueError("SUPABASE_URL not found in environment")
            
            self.supabase: Client = create_client(supabase_url, supabase_key)
            
            # Use BGE-small-en-v1.5 for better performance than all-MiniLM-L6-v2
            logger.info("Initializing BGE-small-en-v1.5 embedding model...")
            self.embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
            logger.info("Memory manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {e}")
            # Fall back to a simpler model if BGE fails
            try:
                logger.warning("Falling back to all-MiniLM-L6-v2 model...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Fallback model loaded successfully")
            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {fallback_error}")
                raise RuntimeError("Could not initialize any embedding model") from fallback_error
        
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text with error handling."""
        try:
            if not text or not text.strip():
                # Return zero vector for empty text
                return [0.0] * 384
            
            embedding = self.embedding_model.encode(text.strip())
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 384
    
    async def store_user_memory(
        self, 
        user_id: str, 
        content: str, 
        memory_type: str = "fact",
        source_conversation_id: str = None,
        importance_score: float = 0.5
    ) -> bool:
        """Store long-term user memory that persists across conversations."""
        try:
            # Validate inputs
            if not content or not content.strip():
                logger.warning("Attempted to store empty or whitespace-only content")
                return False
            
            if not user_id or not user_id.strip():
                logger.warning("Attempted to store memory with empty user_id")
                return False
            
            content = content.strip()
            embedding = self._get_embedding(content)
            
            result = self.supabase.table('user_memory_vectors').insert({
                'user_id': user_id,
                'memory_type': memory_type,
                'content': content,
                'source_conversation_id': source_conversation_id,
                'importance_score': importance_score,
                'embedding': embedding
            }).execute()
            
            if result.data:
                logger.info(f"Stored user memory for {user_id}: {content[:50]}...")
                return True
            else:
                logger.warning("Supabase insert returned no data")
                return False
            
        except Exception as e:
            logger.error(f"Error storing user memory: {e}")
            return False
    
    async def store_conversation_memory(
        self,
        user_id: str,
        conversation_id: str,
        content: str,
        role: str,
        turn_number: int = None,
        message_id: str = None
    ) -> bool:
        """Store conversation-specific memory with validation."""
        try:
            # Validate inputs
            if not content or not content.strip():
                logger.warning("Attempted to store empty conversation content")
                return False
            
            if not user_id or not user_id.strip():
                logger.warning("Attempted to store conversation memory with empty user_id")
                return False
                
            if not conversation_id or not conversation_id.strip():
                logger.warning("Attempted to store conversation memory with empty conversation_id")
                return False
            
            content = content.strip()
            embedding = self._get_embedding(content)
            
            insert_data = {
                'user_id': user_id,
                'conversation_id': conversation_id,
                'content': content,
                'role': role,
                'embedding': embedding
            }
            
            if turn_number is not None:
                insert_data['turn_number'] = turn_number
            if message_id:
                insert_data['message_id'] = message_id
            
            result = self.supabase.table('conversation_memory_vectors').insert(insert_data).execute()
            
            if result.data:
                logger.info(f"Stored conversation memory for {user_id}/{conversation_id}")
                return True
            else:
                logger.warning("Conversation memory insert returned no data")
                return False
            
        except Exception as e:
            logger.error(f"Error storing conversation memory: {e}")
            return False
    
    async def update_conversation_summary(
        self,
        user_id: str,
        conversation_id: str,
        title: str = None,
        summary: str = None,
        key_topics: List[str] = None,
        message_count: int = None
    ) -> bool:
        """Update or create conversation summary."""
        try:
            # Check if summary exists
            existing = self.supabase.table('conversation_summaries')\
                .select('id')\
                .eq('user_id', user_id)\
                .eq('conversation_id', conversation_id)\
                .execute()
            
            update_data = {
                'last_activity': 'NOW()'
            }
            
            if title:
                update_data['title'] = title
            if summary:
                update_data['summary'] = summary
                update_data['summary_embedding'] = self._get_embedding(summary)
            if key_topics:
                update_data['key_topics'] = key_topics
            if message_count is not None:
                update_data['message_count'] = message_count
            
            if existing.data:
                # Update existing
                result = self.supabase.table('conversation_summaries')\
                    .update(update_data)\
                    .eq('user_id', user_id)\
                    .eq('conversation_id', conversation_id)\
                    .execute()
            else:
                # Create new
                insert_data = {
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'title': title or f"Conversation {conversation_id[:8]}",
                    'summary': summary or "",
                    'key_topics': key_topics or [],
                    'message_count': message_count or 0
                }
                if summary:
                    insert_data['summary_embedding'] = self._get_embedding(summary)
                    
                result = self.supabase.table('conversation_summaries')\
                    .insert(insert_data)\
                    .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating conversation summary: {e}")
            return False
    
    async def search_user_memory(
        self,
        user_id: str,
        query: str,
        memory_types: List[str] = None,
        match_threshold: float = 0.7,
        match_count: int = 10
    ) -> List[Dict[str, Any]]:
        """Search user memory across all conversations."""
        try:
            query_embedding = self._get_embedding(query)
            memory_types = memory_types or ['preference', 'fact', 'context']
            
            result = self.supabase.rpc('search_user_memory', {
                'query_embedding': query_embedding,
                'target_user_id': user_id,
                'memory_types': memory_types,
                'match_threshold': match_threshold,
                'match_count': match_count
            }).execute()
            
            memories = result.data or []
            
            # Update access count for retrieved memories
            for memory in memories:
                asyncio.create_task(self._update_memory_access(memory['id']))
            
            logger.info(f"Found {len(memories)} user memories for query: {query[:30]}...")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching user memory: {e}")
            return []
    
    async def search_conversation_memory(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        match_threshold: float = 0.7,
        match_count: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memory within a specific conversation."""
        try:
            query_embedding = self._get_embedding(query)
            
            result = self.supabase.rpc('search_conversation_memory', {
                'query_embedding': query_embedding,
                'target_user_id': user_id,
                'target_conversation_id': conversation_id,
                'match_threshold': match_threshold,
                'match_count': match_count
            }).execute()
            
            memories = result.data or []
            logger.info(f"Found {len(memories)} conversation memories for {conversation_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching conversation memory: {e}")
            return []
    
    async def search_conversation_summaries(
        self,
        user_id: str,
        query: str,
        match_threshold: float = 0.6,
        match_count: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant past conversations."""
        try:
            query_embedding = self._get_embedding(query)
            
            result = self.supabase.rpc('search_conversation_summaries', {
                'query_embedding': query_embedding,
                'target_user_id': user_id,
                'match_threshold': match_threshold,
                'match_count': match_count
            }).execute()
            
            summaries = result.data or []
            logger.info(f"Found {len(summaries)} relevant past conversations")
            return summaries
            
        except Exception as e:
            logger.error(f"Error searching conversation summaries: {e}")
            return []
    
    async def get_comprehensive_context(
        self,
        user_id: str,
        conversation_id: str,
        current_query: str,
        max_user_memories: int = 5,
        max_conversation_memories: int = 8,
        max_past_conversations: int = 3
    ) -> Dict[str, Any]:
        """Get comprehensive context combining all memory levels."""
        try:
            # Search all memory levels in parallel
            user_memories_task = self.search_user_memory(
                user_id, current_query, match_count=max_user_memories
            )
            conversation_memories_task = self.search_conversation_memory(
                user_id, conversation_id, current_query, match_count=max_conversation_memories
            )
            past_conversations_task = self.search_conversation_summaries(
                user_id, current_query, match_count=max_past_conversations
            )
            
            user_memories, conversation_memories, past_conversations = await asyncio.gather(
                user_memories_task,
                conversation_memories_task,
                past_conversations_task,
                return_exceptions=True
            )
            
            # Handle any exceptions
            user_memories = user_memories if not isinstance(user_memories, Exception) else []
            conversation_memories = conversation_memories if not isinstance(conversation_memories, Exception) else []
            past_conversations = past_conversations if not isinstance(past_conversations, Exception) else []
            
            context = {
                'user_memories': user_memories,
                'conversation_memories': conversation_memories,
                'past_conversations': past_conversations,
                'context_summary': self._generate_context_summary(
                    user_memories, conversation_memories, past_conversations
                )
            }
            
            logger.info(f"Generated comprehensive context: {len(user_memories)} user + {len(conversation_memories)} conv + {len(past_conversations)} past")
            return context
            
        except Exception as e:
            logger.error(f"Error getting comprehensive context: {e}")
            return {
                'user_memories': [],
                'conversation_memories': [],
                'past_conversations': [],
                'context_summary': ""
            }
    
    def _generate_context_summary(
        self,
        user_memories: List[Dict],
        conversation_memories: List[Dict],
        past_conversations: List[Dict]
    ) -> str:
        """Generate a readable context summary."""
        summary_parts = []
        
        if user_memories:
            user_facts = [m['content'] for m in user_memories[:3]]
            summary_parts.append(f"User background: {'; '.join(user_facts)}")
        
        if conversation_memories:
            recent_context = [m['content'] for m in conversation_memories[:3]]
            summary_parts.append(f"Recent conversation: {'; '.join(recent_context)}")
        
        if past_conversations:
            past_topics = [c.get('summary', c.get('title', ''))[:50] for c in past_conversations[:2]]
            summary_parts.append(f"Previous discussions: {'; '.join(past_topics)}")
        
        return " | ".join(summary_parts)
    
    async def _update_memory_access(self, memory_id: str):
        """Update memory access count and importance."""
        try:
            self.supabase.rpc('update_memory_access', {
                'memory_id': memory_id
            }).execute()
        except Exception as e:
            logger.error(f"Error updating memory access: {e}")
    
    async def extract_and_store_user_facts(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        role: str = "user"
    ):
        """Extract important user facts from a message and store them."""
        if role != "user":
            return
        
        # Simple fact extraction patterns
        fact_patterns = [
            ("name", ["my name is", "i'm", "i am", "call me"]),
            ("location", ["i live in", "i'm from", "based in", "located in"]),
            ("work", ["i work as", "my job is", "i'm a", "profession"]),
            ("hobby", ["hobby", "hobbies", "i like", "i enjoy", "i love"]),
            ("preference", ["i prefer", "i like", "i hate", "i don't like"])
        ]
        
        message_lower = message.lower()
        
        for fact_type, patterns in fact_patterns:
            for pattern in patterns:
                if pattern in message_lower:
                    # Extract the relevant part after the pattern
                    parts = message_lower.split(pattern)
                    if len(parts) > 1:
                        fact_content = f"User {pattern} {parts[1].split('.')[0].strip()}"
                        await self.store_user_memory(
                            user_id=user_id,
                            content=fact_content,
                            memory_type="fact",
                            source_conversation_id=conversation_id,
                            importance_score=0.8
                        )
                        break

# Global instance
memory_manager = HierarchicalMemoryManager()