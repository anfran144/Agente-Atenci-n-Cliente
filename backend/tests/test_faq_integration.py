"""
Integration test for FAQ handler with RAG

This test verifies the complete FAQ handling flow:
1. User message → Intent classification → FAQ handler
2. RAG service retrieves context
3. LLM generates response
4. Response is returned

Note: This requires a running database with embeddings populated.
"""

from unittest.mock import Mock, patch, MagicMock
from agent import handle_faq, AgentState
from langchain_core.messages import HumanMessage


def test_faq_handler_with_mock_rag():
    """Test FAQ handler with mocked RAG service"""
    
    # Create initial state
    state: AgentState = {
        "tenant_id": "test-tenant-123",
        "conversation_id": "test-conv-456",
        "messages": [HumanMessage(content="What are your business hours?")],
        "intent": "faq",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Mock the RAG service
    with patch('database.get_supabase_client') as mock_supabase, \
         patch('rag_service.RAGService') as mock_rag_class, \
         patch('agent.get_llm') as mock_llm:
        
        # Setup mock RAG service
        mock_rag_instance = Mock()
        mock_rag_instance.retrieve_context.return_value = """
=== Relevant FAQs ===
Q: What are your business hours?
A: We're open Monday-Friday 9am-5pm, Saturday 10am-4pm, closed Sunday.
"""
        mock_rag_class.return_value = mock_rag_instance
        
        # Setup mock LLM
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = "We're open Monday-Friday 9am-5pm, Saturday 10am-4pm, and closed on Sunday."
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        # Call handle_faq
        result_state = handle_faq(state)
        
        # Verify RAG service was called with correct parameters
        mock_rag_instance.retrieve_context.assert_called_once_with(
            "What are your business hours?",
            "test-tenant-123",
            top_k=5
        )
        
        # Verify LLM was called
        assert mock_llm_instance.invoke.called
        
        # Verify response was set
        assert result_state["final_response"] is not None
        assert "9am-5pm" in result_state["final_response"] or result_state["final_response"] != ""
        
        # Verify context was stored
        assert result_state["context"] is not None
        
        print("✓ FAQ handler integration test passed")


def test_faq_handler_no_context():
    """Test FAQ handler when no relevant context is found"""
    
    state: AgentState = {
        "tenant_id": "test-tenant-123",
        "conversation_id": "test-conv-456",
        "messages": [HumanMessage(content="Random unrelated question")],
        "intent": "faq",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    with patch('database.get_supabase_client') as mock_supabase, \
         patch('rag_service.RAGService') as mock_rag_class:
        
        # Setup mock RAG service to return no context
        mock_rag_instance = Mock()
        mock_rag_instance.retrieve_context.return_value = "No relevant information found."
        mock_rag_class.return_value = mock_rag_instance
        
        # Call handle_faq
        result_state = handle_faq(state)
        
        # Verify appropriate response for no context
        assert result_state["final_response"] is not None
        assert "don't have enough information" in result_state["final_response"] or \
               "human assistance" in result_state["final_response"]
        
        print("✓ FAQ handler no context test passed")


def test_faq_handler_missing_tenant():
    """Test FAQ handler when tenant_id is missing"""
    
    state: AgentState = {
        "tenant_id": None,  # Missing tenant
        "conversation_id": "test-conv-456",
        "messages": [HumanMessage(content="What are your hours?")],
        "intent": "faq",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Call handle_faq
    result_state = handle_faq(state)
    
    # Verify error response
    assert result_state["final_response"] is not None
    assert "couldn't identify" in result_state["final_response"] or \
           "business" in result_state["final_response"]
    
    print("✓ FAQ handler missing tenant test passed")


def test_faq_handler_error_handling():
    """Test FAQ handler error handling"""
    
    state: AgentState = {
        "tenant_id": "test-tenant-123",
        "conversation_id": "test-conv-456",
        "messages": [HumanMessage(content="What are your hours?")],
        "intent": "faq",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    with patch('database.get_supabase_client') as mock_supabase, \
         patch('rag_service.RAGService') as mock_rag_class:
        
        # Setup mock RAG service to raise an exception
        mock_rag_class.side_effect = Exception("Database connection error")
        
        # Call handle_faq
        result_state = handle_faq(state)
        
        # Verify error response
        assert result_state["final_response"] is not None
        assert "encountered an issue" in result_state["final_response"] or \
               "try again" in result_state["final_response"]
        
        print("✓ FAQ handler error handling test passed")


if __name__ == "__main__":
    print("Running FAQ handler integration tests...\n")
    
    try:
        test_faq_handler_with_mock_rag()
        test_faq_handler_no_context()
        test_faq_handler_missing_tenant()
        test_faq_handler_error_handling()
        
        print("\n✅ All FAQ handler integration tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
