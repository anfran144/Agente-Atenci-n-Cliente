"""
Integration tests for response generator with complete workflow

This module tests the complete agent workflow including response generation
to ensure all components work together correctly.

Requirements: 1.4, 3.4
"""
import pytest
from agent import agent, AgentState
from langchain_core.messages import HumanMessage


def test_complete_workflow_with_other_intent():
    """Test complete workflow for 'other' intent generates helpful response"""
    initial_state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="Hello")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = agent.invoke(initial_state)
    
    # Verify intent was classified
    assert result["intent"] == "other"
    
    # Verify response was generated
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 0
    
    # Verify response is helpful
    response_lower = result["final_response"].lower()
    assert "help" in response_lower or "assist" in response_lower


def test_complete_workflow_preserves_handler_response():
    """Test that workflow preserves responses set by handler nodes"""
    # This test uses a simple state to verify the flow
    initial_state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="Thanks for the great service!")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = agent.invoke(initial_state)
    
    # Verify intent was classified as review
    assert result["intent"] in ["review", "complaint"]
    
    # Verify a response was generated
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 0


def test_response_generator_handles_all_intents():
    """Test that response generator handles all possible intents"""
    test_messages = [
        ("What are your hours?", "faq"),
        ("I want to order pizza", "order_create"),
        ("The food was cold", "complaint"),
        ("Excellent service!", "review"),
        ("Hello", "other"),
    ]
    
    for message, expected_intent_category in test_messages:
        initial_state = {
            "tenant_id": "test-tenant",
            "conversation_id": "test-conv",
            "messages": [HumanMessage(content=message)],
            "intent": None,
            "context": None,
            "order_draft": None,
            "requires_confirmation": False,
            "final_response": None
        }
        
        result = agent.invoke(initial_state)
        
        # Verify response was generated
        assert result["final_response"] is not None, f"No response for: {message}"
        assert len(result["final_response"]) > 0, f"Empty response for: {message}"
        
        # Verify intent was classified
        assert result["intent"] is not None, f"No intent for: {message}"


def test_response_generator_error_handling():
    """Test that response generator handles errors gracefully"""
    # Test with minimal state
    initial_state = {
        "tenant_id": None,
        "conversation_id": None,
        "messages": [],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = agent.invoke(initial_state)
    
    # Should still generate a response even with minimal state
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 0


def test_response_formatting_consistency():
    """Test that responses are consistently formatted"""
    test_cases = [
        "What time do you close?",
        "I'd like to order",
        "Great experience!",
        "Hi there",
    ]
    
    for message in test_cases:
        initial_state = {
            "tenant_id": "test-tenant",
            "conversation_id": "test-conv",
            "messages": [HumanMessage(content=message)],
            "intent": None,
            "context": None,
            "order_draft": None,
            "requires_confirmation": False,
            "final_response": None
        }
        
        result = agent.invoke(initial_state)
        response = result["final_response"]
        
        # Verify response exists and is non-empty
        assert response is not None
        assert len(response) > 0
        
        # Verify response is a string
        assert isinstance(response, str)
        
        # Verify response has reasonable length (not too short)
        assert len(response) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
