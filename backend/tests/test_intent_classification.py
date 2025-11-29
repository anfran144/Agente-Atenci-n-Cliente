"""
Test intent classification functionality.

This test verifies that the classify_intent node correctly classifies
user messages into the appropriate intent categories.
"""

import pytest
from langchain_core.messages import HumanMessage
from agent import classify_intent, AgentState


def test_classify_faq_intent():
    """Test classification of FAQ messages."""
    state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="What time do you close?")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = classify_intent(state)
    assert result["intent"] == "faq"


def test_classify_order_create_intent():
    """Test classification of order creation messages."""
    state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="I'd like to order 2 pizzas")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = classify_intent(state)
    assert result["intent"] == "order_create"


def test_classify_complaint_intent():
    """Test classification of complaint messages."""
    state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="My food arrived cold")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = classify_intent(state)
    assert result["intent"] == "complaint"


def test_classify_review_intent():
    """Test classification of review messages."""
    state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="The service was excellent, 5 stars!")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = classify_intent(state)
    assert result["intent"] == "review"


def test_classify_other_intent():
    """Test classification of unclear messages."""
    state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="Hello")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = classify_intent(state)
    assert result["intent"] == "other"


def test_classify_spanish_faq():
    """Test classification of Spanish FAQ messages."""
    state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="¿Cuáles son sus horarios?")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = classify_intent(state)
    assert result["intent"] == "faq"


def test_classify_empty_messages():
    """Test classification with empty messages list."""
    state = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = classify_intent(state)
    assert result["intent"] == "other"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
