"""
Tests for RAG Service

These tests verify the RAG service functionality including:
- Embedding generation
- Vector similarity search
- Context retrieval with tenant filtering
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from rag_service import RAGService


class TestRAGService:
    """Test suite for RAG Service"""
    
    def test_rag_service_initialization(self):
        """Test RAG service initializes correctly"""
        mock_client = Mock()
        
        rag_service = RAGService(mock_client)
        
        assert rag_service.supabase == mock_client
        assert rag_service.embeddings_model is not None
        assert rag_service.embedding_dim > 0
    
    def test_generate_embedding(self):
        """Test embedding generation produces correct format"""
        mock_client = Mock()
        rag_service = RAGService(mock_client)
        
        text = "What are your business hours?"
        embedding = rag_service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == rag_service.embedding_dim
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_embedding_different_texts(self):
        """Test that different texts produce different embeddings"""
        mock_client = Mock()
        rag_service = RAGService(mock_client)
        
        text1 = "What are your hours?"
        text2 = "Do you accept credit cards?"
        
        embedding1 = rag_service.generate_embedding(text1)
        embedding2 = rag_service.generate_embedding(text2)
        
        # Embeddings should be different
        assert embedding1 != embedding2
    
    def test_search_faqs_with_results(self):
        """Test FAQ search returns results correctly"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [
            {
                "id": "faq-1",
                "question": "What are your hours?",
                "answer": "We're open 9am-5pm",
                "similarity": 0.95
            }
        ]
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        rag_service = RAGService(mock_client)
        query_embedding = [0.1] * rag_service.embedding_dim
        
        results = rag_service.search_faqs(query_embedding, "tenant-123", top_k=3)
        
        assert len(results) == 1
        assert results[0]["question"] == "What are your hours?"
        mock_client.rpc.assert_called_once()
    
    def test_search_faqs_handles_errors(self):
        """Test FAQ search handles errors gracefully"""
        mock_client = Mock()
        mock_client.rpc.side_effect = Exception("Database error")
        
        rag_service = RAGService(mock_client)
        query_embedding = [0.1] * rag_service.embedding_dim
        
        results = rag_service.search_faqs(query_embedding, "tenant-123", top_k=3)
        
        # Should return empty list on error
        assert results == []
    
    def test_search_products_with_results(self):
        """Test product search returns results correctly"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [
            {
                "id": "prod-1",
                "name": "Pizza Margherita",
                "description": "Classic pizza",
                "price": 12.99,
                "similarity": 0.92
            }
        ]
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        rag_service = RAGService(mock_client)
        query_embedding = [0.1] * rag_service.embedding_dim
        
        results = rag_service.search_products(query_embedding, "tenant-123", top_k=3)
        
        assert len(results) == 1
        assert results[0]["name"] == "Pizza Margherita"
        mock_client.rpc.assert_called_once()
    
    def test_retrieve_context_combines_results(self):
        """Test retrieve_context combines FAQ and product results"""
        mock_client = Mock()
        
        # Mock FAQ search results
        faq_response = Mock()
        faq_response.data = [
            {
                "question": "What are your hours?",
                "answer": "We're open 9am-5pm"
            }
        ]
        
        # Mock product search results
        product_response = Mock()
        product_response.data = [
            {
                "name": "Pizza",
                "description": "Delicious pizza",
                "price": 12.99,
                "category": "Main"
            }
        ]
        
        # Setup mock to return different responses for different RPC calls
        mock_client.rpc.return_value.execute.side_effect = [faq_response, product_response]
        
        rag_service = RAGService(mock_client)
        context = rag_service.retrieve_context("What do you have?", "tenant-123", top_k=4)
        
        # Context should contain both FAQ and product information
        assert "Relevant FAQs" in context
        assert "What are your hours?" in context
        assert "Relevant Products" in context
        assert "Pizza" in context
    
    def test_retrieve_context_no_results(self):
        """Test retrieve_context handles no results"""
        mock_client = Mock()
        empty_response = Mock()
        empty_response.data = []
        mock_client.rpc.return_value.execute.return_value = empty_response
        
        rag_service = RAGService(mock_client)
        context = rag_service.retrieve_context("Random query", "tenant-123", top_k=4)
        
        assert context == "No relevant information found."
    
    def test_retrieve_context_tenant_filtering(self):
        """Test that retrieve_context passes tenant_id to search functions"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = []
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        rag_service = RAGService(mock_client)
        tenant_id = "tenant-specific-123"
        
        rag_service.retrieve_context("Test query", tenant_id, top_k=4)
        
        # Verify tenant_id was passed in RPC calls
        calls = mock_client.rpc.call_args_list
        for call in calls:
            args, kwargs = call
            # Check the parameters passed to RPC
            if args[0] == 'match_faqs' or args[0] == 'match_products':
                assert args[1]['match_tenant_id'] == tenant_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
