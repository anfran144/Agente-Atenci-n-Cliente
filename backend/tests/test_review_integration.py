"""
Integration test for review handler with full agent workflow

This test verifies that the review handler integrates correctly with:
- Intent classification
- Full agent workflow
- Message persistence

Requirements: 7.1, 7.2, 7.3, 7.4
"""

import pytest
from langchain_core.messages import HumanMessage
from agent import agent, AgentState
from database import get_supabase_client
from repository import Repository


@pytest.fixture
def supabase_client():
    """Get Supabase client for tests"""
    return get_supabase_client()


@pytest.fixture
def repo(supabase_client):
    """Get repository instance"""
    return Repository(supabase_client)


@pytest.fixture
def test_tenant(repo):
    """Get a test tenant"""
    tenants = repo.get_active_tenants()
    assert len(tenants) > 0, "No active tenants found"
    return tenants[0]


def test_complaint_full_workflow(test_tenant, repo):
    """Test complaint handling through full agent workflow"""
    
    # Create conversation
    conversation = repo.create_conversation(
        tenant_id=test_tenant["id"],
        channel="web",
        customer_id="integration_test_1"
    )
    
    complaint_message = "El pedido llegó tarde y la comida estaba fría. Muy mal."
    
    # Create initial state
    initial_state: AgentState = {
        "tenant_id": test_tenant["id"],
        "conversation_id": conversation["id"],
        "messages": [HumanMessage(content=complaint_message)],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Invoke the full agent workflow
    result = agent.invoke(initial_state)
    
    # Verify intent was classified
    assert result["intent"] in ["complaint", "review"], f"Expected complaint/review intent, got {result['intent']}"
    
    # Verify response was generated
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 0
    
    # Verify review was persisted
    reviews = repo.client.table("reviews").select("*").eq("conversation_id", conversation["id"]).execute()
    assert len(reviews.data) > 0, "Review not persisted"
    
    review = reviews.data[0]
    assert review["rating"] <= 2, "Complaint should have low rating"
    assert review["requires_attention"] is True, "Complaint should require attention"
    
    print(f"✓ Complaint workflow: intent={result['intent']}, rating={review['rating']}, requires_attention={review['requires_attention']}")


def test_positive_review_full_workflow(test_tenant, repo):
    """Test positive review handling through full agent workflow"""
    
    # Create conversation
    conversation = repo.create_conversation(
        tenant_id=test_tenant["id"],
        channel="web",
        customer_id="integration_test_2"
    )
    
    review_message = "¡Excelente! Todo perfecto, la mejor experiencia. 5 estrellas."
    
    # Create initial state
    initial_state: AgentState = {
        "tenant_id": test_tenant["id"],
        "conversation_id": conversation["id"],
        "messages": [HumanMessage(content=review_message)],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Invoke the full agent workflow
    result = agent.invoke(initial_state)
    
    # Verify intent was classified
    assert result["intent"] in ["review"], f"Expected review intent, got {result['intent']}"
    
    # Verify response was generated
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 0
    
    # Verify review was persisted
    reviews = repo.client.table("reviews").select("*").eq("conversation_id", conversation["id"]).execute()
    assert len(reviews.data) > 0, "Review not persisted"
    
    review = reviews.data[0]
    assert review["rating"] >= 4, "Positive review should have high rating"
    assert review["requires_attention"] is False, "Positive review should not require attention"
    
    print(f"✓ Positive review workflow: intent={result['intent']}, rating={review['rating']}, requires_attention={review['requires_attention']}")


def test_multiple_reviews_same_conversation(test_tenant, repo):
    """Test that multiple reviews can be recorded in the same conversation"""
    
    # Create conversation
    conversation = repo.create_conversation(
        tenant_id=test_tenant["id"],
        channel="web",
        customer_id="integration_test_3"
    )
    
    # First review (positive)
    initial_state1: AgentState = {
        "tenant_id": test_tenant["id"],
        "conversation_id": conversation["id"],
        "messages": [HumanMessage(content="La comida estuvo muy buena")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result1 = agent.invoke(initial_state1)
    
    # Second review (complaint)
    initial_state2: AgentState = {
        "tenant_id": test_tenant["id"],
        "conversation_id": conversation["id"],
        "messages": [HumanMessage(content="Pero el servicio fue lento")],
        "intent": None,
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    result2 = agent.invoke(initial_state2)
    
    # Verify both reviews were persisted
    reviews = repo.client.table("reviews").select("*").eq("conversation_id", conversation["id"]).order("created_at").execute()
    assert len(reviews.data) >= 2, "Both reviews should be persisted"
    
    print(f"✓ Multiple reviews in same conversation: {len(reviews.data)} reviews recorded")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
