"""
Tests for the response generator node

This module tests the generate_response function to ensure it:
- Formats responses based on intent type
- Handles "other" intent with helpful fallback
- Preserves responses set by handler nodes
- Applies tenant-specific tone (when available)

Requirements: 1.4, 3.4
"""
import pytest
from agent import generate_response, AgentState
from langchain_core.messages import HumanMessage


def test_generate_response_preserves_existing_response():
    """Test that generate_response preserves responses set by handlers"""
    state = AgentState(
        tenant_id="test-tenant",
        conversation_id="test-conv",
        messages=[HumanMessage(content="What are your hours?")],
        intent="faq",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response="We are open Monday to Friday, 9am to 5pm."
    )
    
    result = generate_response(state)
    
    assert result["final_response"] == "We are open Monday to Friday, 9am to 5pm."


def test_generate_response_handles_other_intent():
    """Test that generate_response provides helpful fallback for 'other' intent"""
    state = AgentState(
        tenant_id="test-tenant",
        conversation_id="test-conv",
        messages=[HumanMessage(content="Hello")],
        intent="other",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result = generate_response(state)
    
    # Should provide helpful information about what the agent can do
    assert result["final_response"] is not None
    assert "help" in result["final_response"].lower()
    assert len(result["final_response"]) > 0


def test_generate_response_fallback_for_faq():
    """Test fallback response for FAQ intent when handler didn't set response"""
    state = AgentState(
        tenant_id="test-tenant",
        conversation_id="test-conv",
        messages=[HumanMessage(content="What's your address?")],
        intent="faq",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result = generate_response(state)
    
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 0


def test_generate_response_fallback_for_order():
    """Test fallback response for order intent when handler didn't set response"""
    state = AgentState(
        tenant_id="test-tenant",
        conversation_id="test-conv",
        messages=[HumanMessage(content="I want to order pizza")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result = generate_response(state)
    
    assert result["final_response"] is not None
    assert "order" in result["final_response"].lower()


def test_generate_response_fallback_for_review():
    """Test fallback response for review intent when handler didn't set response"""
    state = AgentState(
        tenant_id="test-tenant",
        conversation_id="test-conv",
        messages=[HumanMessage(content="Great service!")],
        intent="review",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result = generate_response(state)
    
    assert result["final_response"] is not None
    assert "feedback" in result["final_response"].lower() or "thank" in result["final_response"].lower()


def test_generate_response_always_sets_response():
    """Test that generate_response always sets a final_response"""
    state = AgentState(
        tenant_id="test-tenant",
        conversation_id="test-conv",
        messages=[],
        intent=None,
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result = generate_response(state)
    
    # Should always have a response, even with minimal state
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
