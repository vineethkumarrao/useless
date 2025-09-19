"""
Enhanced Vector Memory System using ChromaDB and BGE embeddings
This replaces the Supabase vector approach with a local, faster solution.
"""

import os
import uuid
import pandas as pd
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document


class BGEEmbeddings(Embeddings):
    """BGE embedding model wrapper for LangChain compatibility."""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """Initialize BGE embeddings model."""
        print(f"[VECTOR] Loading BGE embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"[VECTOR] BGE model loaded successfully")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        embedding = self.model.encode([text], convert_to_tensor=False)
        return embedding[0].tolist()


class VectorMemorySystem:
    """Enhanced conversation memory using ChromaDB."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize the vector memory system."""
        self.persist_directory = persist_directory
        
        # Initialize BGE embeddings
        self.embeddings = BGEEmbeddings()
        
        # Initialize ChromaDB client
        print(f"[VECTOR] Initializing ChromaDB at: {persist_directory}")
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get conversation collection
        self.collection_name = "conversations"
        try:
            self.collection = self.client.get_collection(self.collection_name)
            print(f"[VECTOR] Using existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Conversation memory for chatbot"}
            )
            print(f"[VECTOR] Created new collection: {self.collection_name}")
        
        # Initialize LangChain Chroma wrapper
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings
        )
        
        print(f"[VECTOR] VectorMemorySystem initialized successfully")
    
    async def store_message(
        self, 
        user_id: str, 
        conversation_id: str, 
        message: str, 
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a conversation message in vector memory."""
        try:
            # Create document
            doc_id = str(uuid.uuid4())
            
            # Prepare metadata
            doc_metadata = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "role": role,
                "message_id": doc_id,
                "timestamp": str(pd.Timestamp.now())
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            # Create document
            document = Document(
                page_content=message,
                metadata=doc_metadata
            )
            
            # Add to vectorstore
            self.vectorstore.add_documents([document], ids=[doc_id])
            
            print(f"[VECTOR] Stored message: {role} - {message[:50]}...")
            return doc_id
            
        except Exception as e:
            print(f"[VECTOR] Error storing message: {e}")
            return None
    
    async def retrieve_context(
        self, 
        user_id: str, 
        conversation_id: str, 
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> str:
        """Retrieve relevant conversation context."""
        try:
            # Search for similar messages - use proper ChromaDB filter syntax
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=max_results,
                filter={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"conversation_id": {"$eq": conversation_id}}
                    ]
                }
            )
            
            if not results:
                print(f"[VECTOR] No context found for conversation: {conversation_id}")
                return ""
            
            # Filter by similarity threshold and format context
            context_messages = []
            for doc, score in results:
                # ChromaDB uses distance (lower = more similar)
                similarity = 1 - score
                if similarity >= similarity_threshold:
                    role = doc.metadata.get('role', 'unknown')
                    message = doc.page_content
                    context_messages.append(f"{role}: {message}")
            
            if context_messages:
                context = "\n".join(context_messages[-3:])  # Last 3 relevant messages
                print(f"[VECTOR] Retrieved {len(context_messages)} relevant messages")
                return f"Previous conversation:\n{context}"
            else:
                print(f"[VECTOR] No messages met similarity threshold")
                return ""
                
        except Exception as e:
            print(f"[VECTOR] Error retrieving context: {e}")
            return ""
    
    def get_conversation_stats(self, user_id: str, conversation_id: str) -> Dict[str, int]:
        """Get statistics about a conversation."""
        try:
            # Query collection directly for stats - proper ChromaDB filter syntax
            results = self.collection.get(
                where={
                    "$and": [
                        {"user_id": {"$eq": user_id}},
                        {"conversation_id": {"$eq": conversation_id}}
                    ]
                },
                include=["metadatas"]
            )
            
            total_messages = len(results['ids']) if results['ids'] else 0
            user_messages = sum(1 for meta in results['metadatas'] if meta.get('role') == 'user')
            assistant_messages = sum(1 for meta in results['metadatas'] if meta.get('role') == 'assistant')
            
            return {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages
            }
            
        except Exception as e:
            print(f"[VECTOR] Error getting conversation stats: {e}")
            return {"total_messages": 0, "user_messages": 0, "assistant_messages": 0}


# Global instance
vector_memory = None

def get_vector_memory() -> VectorMemorySystem:
    """Get or create the global vector memory instance."""
    global vector_memory
    if vector_memory is None:
        vector_memory = VectorMemorySystem()
    return vector_memory


# Helper functions for backward compatibility
async def store_chat_vector(user_id: str, conversation_id: str, message: str, role: str) -> str:
    """Store a chat message in vector memory."""
    memory = get_vector_memory()
    return await memory.store_message(user_id, conversation_id, message, role)


async def retrieve_chat_context(user_id: str, conversation_id: str, query: str) -> str:
    """Retrieve relevant chat context."""
    memory = get_vector_memory()
    return await memory.retrieve_context(user_id, conversation_id, query)


if __name__ == "__main__":
    import asyncio
    import pandas as pd  # Add this import for timestamp
    
    async def test_vector_memory():
        """Test the vector memory system."""
        print("🧪 Testing Vector Memory System")
        
        # Initialize
        memory = VectorMemorySystem()
        
        # Test data
        user_id = "test_user_123"
        conversation_id = "test_conv_456"
        
        # Store some messages
        await memory.store_message(user_id, conversation_id, "My name is Alice and I love programming", "user")
        await memory.store_message(user_id, conversation_id, "Nice to meet you Alice! Programming is awesome.", "assistant")
        await memory.store_message(user_id, conversation_id, "I work as a software engineer at Google", "user")
        await memory.store_message(user_id, conversation_id, "That's impressive! Google is a great company for engineers.", "assistant")
        
        # Test retrieval
        context = await memory.retrieve_context(user_id, conversation_id, "What's my name and job?")
        print(f"📝 Retrieved context:\n{context}")
        
        # Test stats
        stats = memory.get_conversation_stats(user_id, conversation_id)
        print(f"📊 Conversation stats: {stats}")
        
        print("✅ Vector Memory System test completed!")
    
    # Add pandas import at the top
    import pandas as pd
    asyncio.run(test_vector_memory())