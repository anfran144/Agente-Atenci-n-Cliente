"""
RAG (Retrieval-Augmented Generation) Service for FAQ handling

This module implements the RAG service that:
1. Generates embeddings for user queries
2. Performs vector similarity search in faqs_embeddings and products_embeddings
3. Retrieves relevant context filtered by tenant_id
4. Returns top-k most relevant documents

Requirements: 1.1, 1.2, 1.3
"""

import os
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from supabase import Client
from dotenv import load_dotenv

load_dotenv()


class RAGService:
    """
    Service for Retrieval-Augmented Generation using vector embeddings.
    
    This service handles embedding generation and vector similarity search
    to retrieve relevant context for FAQ responses.
    """
    
    def __init__(self, supabase_client: Client, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initialize RAG service with Supabase client and embeddings model.
        
        Args:
            supabase_client: Supabase client for database operations
            model_name: Name of the sentence-transformers model to use
                       Default is "all-mpnet-base-v2" which produces 768-dim embeddings
                       Note: Schema uses vector(1536) but we can work with smaller dimensions
        """
        self.supabase = supabase_client
        self.embeddings_model = SentenceTransformer(model_name)
        self.embedding_dim = self.embeddings_model.get_sentence_embedding_dimension()
        print(f"RAG Service initialized with {model_name} (dimension: {self.embedding_dim})")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a text query.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        embedding = self.embeddings_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def search_faqs(
        self, 
        query_embedding: List[float], 
        tenant_id: str, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for similar FAQs using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            tenant_id: Tenant ID to filter results
            top_k: Number of results to return
            
        Returns:
            List of FAQ documents with similarity scores
        """
        try:
            # Use Supabase RPC for vector similarity search
            # The RPC function performs cosine similarity search
            result = self.supabase.rpc(
                'match_faqs',
                {
                    'query_embedding': query_embedding,
                    'match_tenant_id': tenant_id,
                    'match_count': top_k
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"FAQ search error: {e}")
            # Fallback: return empty list if RPC fails
            return []
    
    def search_products(
        self, 
        query_embedding: List[float], 
        tenant_id: str, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for similar products using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            tenant_id: Tenant ID to filter results
            top_k: Number of results to return
            
        Returns:
            List of product documents with similarity scores
        """
        try:
            # Use Supabase RPC for vector similarity search
            result = self.supabase.rpc(
                'match_products',
                {
                    'query_embedding': query_embedding,
                    'match_tenant_id': tenant_id,
                    'match_count': top_k
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Product search error: {e}")
            # Fallback: return empty list if RPC fails
            return []
    
    def retrieve_context(
        self, 
        query: str, 
        tenant_id: str, 
        top_k: int = 5
    ) -> str:
        """
        Retrieve relevant context for a query using RAG.
        
        This method:
        1. Generates embedding for the query
        2. Searches both FAQs and products tables
        3. Combines and ranks results
        4. Returns formatted context string
        
        Requirements 1.1, 1.2, 1.3: RAG with tenant filtering
        
        Args:
            query: User's question or message
            tenant_id: Tenant ID to filter results
            top_k: Total number of documents to retrieve
            
        Returns:
            Formatted context string with relevant information
        """
        # Generate embedding for the query
        query_embedding = self.generate_embedding(query)
        
        # Search both FAQs and products (split top_k between them)
        faq_results = self.search_faqs(query_embedding, tenant_id, top_k // 2 + 1)
        product_results = self.search_products(query_embedding, tenant_id, top_k // 2 + 1)
        
        # Format context from results
        context_parts = []
        
        # Add FAQ context
        if faq_results:
            context_parts.append("=== Relevant FAQs ===")
            for faq in faq_results[:top_k // 2 + 1]:
                question = faq.get('question', '')
                answer = faq.get('answer', '')
                if question and answer:
                    context_parts.append(f"Q: {question}")
                    context_parts.append(f"A: {answer}")
                    context_parts.append("")
        
        # Add product context
        if product_results:
            context_parts.append("=== Relevant Products ===")
            for product in product_results[:top_k // 2 + 1]:
                name = product.get('name', '')
                description = product.get('description', '')
                price = product.get('price', '')
                category = product.get('category', '')
                
                if name:
                    product_info = f"Product: {name}"
                    if category:
                        product_info += f" (Category: {category})"
                    if price:
                        product_info += f" - Price: ${price}"
                    context_parts.append(product_info)
                    
                    if description:
                        context_parts.append(f"Description: {description}")
                    context_parts.append("")
        
        # Join all context parts
        context = "\n".join(context_parts)
        
        return context if context.strip() else "No relevant information found."
