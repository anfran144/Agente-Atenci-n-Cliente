"""
Tests for LangGraph Agent Foundation

Verifies that the agent workflow is properly configured with
all required nodes, edges, and state management.
"""

import pytest
from agent import (
    AgentState,
    create_agent_workflow,
    compile_agent,
    classify_intent,
    handle_faq,
    handle_order,
    handle_review,
    generate_response,
    route_by_intent
)
from langchain_core.messages import HumanMessage


def test_agent_state_structure():
    """Test that AgentState has all required fields"""
    state: AgentState = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Verify all required fields are present
    assert "tenant_id" in state
    assert "conversation_id" in state
    assert "messages" in state
    assert "intent" in state
    assert "context" in state
    assert "order_draft" in state
    assert "requires_confirmation" in state
    assert "final_response" in state


def test_classify_intent_node():
    """Test that classify_intent node updates state correctly"""
    state: AgentState = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="What are your hours?")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = classify_intent(state)
    
    # Verify intent is set (placeholder sets to "other")
    assert result["intent"] is not None
    assert isinstance(result["intent"], str)


def test_handle_faq_node():
    """Test that handle_faq node generates a response"""
    state: AgentState = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="What are your hours?")],
        "intent": "faq",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = handle_faq(state)
    
    # Verify response is generated
    assert result["final_response"] is not None


def test_handle_order_node():
    """Test that handle_order node processes order requests"""
    state: AgentState = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="I want to order a pizza")],
        "intent": "order_create",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = handle_order(state)
    
    # Verify response is generated
    assert result["final_response"] is not None
    assert "requires_confirmation" in result


def test_handle_review_node():
    """Test that handle_review node processes reviews"""
    state: AgentState = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="Great service!")],
        "intent": "review",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = handle_review(state)
    
    # Verify response is generated
    assert result["final_response"] is not None


def test_generate_response_node():
    """Test that generate_response node creates final response"""
    state: AgentState = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv",
        "messages": [HumanMessage(content="Hello")],
        "intent": "other",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result = generate_response(state)
    
    # Verify final response is set
    assert result["final_response"] is not None
    assert isinstance(result["final_response"], str)


def test_route_by_intent():
    """Test that intent routing works correctly"""
    # Test FAQ routing
    state_faq: AgentState = {"intent": "faq"}
    assert route_by_intent(state_faq) == "faq"
    
    # Test order routing
    state_order_create: AgentState = {"intent": "order_create"}
    assert route_by_intent(state_order_create) == "order"
    
    state_order_update: AgentState = {"intent": "order_update"}
    assert route_by_intent(state_order_update) == "order"
    
    # Test review routing
    state_complaint: AgentState = {"intent": "complaint"}
    assert route_by_intent(state_complaint) == "review"
    
    state_review: AgentState = {"intent": "review"}
    assert route_by_intent(state_review) == "review"
    
    # Test other routing
    state_other: AgentState = {"intent": "other"}
    assert route_by_intent(state_other) == "respond"
    
    # Test missing intent
    state_none: AgentState = {}
    assert route_by_intent(state_none) == "respond"


def test_create_agent_workflow():
    """Test that workflow is created with all nodes and edges"""
    workflow = create_agent_workflow()
    
    # Verify workflow is created
    assert workflow is not None
    
    # Verify nodes are added (check internal structure)
    assert "classify" in workflow.nodes
    assert "faq" in workflow.nodes
    assert "order" in workflow.nodes
    assert "review" in workflow.nodes
    assert "respond" in workflow.nodes


def test_compile_agent():
    """Test that agent compiles successfully"""
    agent = compile_agent()
    
    # Verify agent is compiled
    assert agent is not None


def test_agent_execution_basic():
    """Test basic agent execution with a simple message"""
    agent = compile_agent()
    
    initial_state: AgentState = {
        "tenant_id": "test-tenant",
        "conversation_id": "test-conv-123",
        "messages": [HumanMessage(content="Hello")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Execute the agent
    result = agent.invoke(initial_state)
    
    # Verify execution completes and produces a response
    assert result is not None
    assert "final_response" in result
    assert result["final_response"] is not None
    assert "intent" in result
    assert result["intent"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
