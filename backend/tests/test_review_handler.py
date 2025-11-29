"""
Test suite for review and complaint handler

This test verifies that the review handler correctly:
- Classifies complaints vs positive reviews
- Extracts ratings appropriately
- Persists reviews to the database
- Sets requires_attention flag for complaints
- Generates empathetic responses

Requirements: 7.1, 7.2, 7.3, 7.4
"""

import pytest
from langchain_core.messages import HumanMessage
from agent import handle_review, AgentState
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


@pytest.fixture
def test_conversation(repo, test_tenant):
    """Create a test conversation"""
    conversation = repo.create_conversation(
        tenant_id=test_tenant["id"],
        channel="web",
        customer_id="test_customer"
    )
    return conversation


def test_complaint_handling(test_tenant, test_conversation, repo):
    """Test that complaints are properly classified and persisted with requires_attention flag"""
    # Requirement 7.1, 7.3: Complaints should be marked with requires_attention
    
    complaint_message = "La comida estaba horrible y llegó fría. Muy mal servicio."
    
    state: AgentState = {
        "tenant_id": test_tenant["id"],
        "conversation_id": test_conversation["id"],
        "messages": [HumanMessage(content=complaint_message)],
        "intent": "complaint",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Handle the complaint
    result_state = handle_review(state)
    
    # Verify response is empathetic
    assert result_state["final_response"] is not None
    assert "sorry" in result_state["final_response"].lower() or "apologize" in result_state["final_response"].lower()
    
    # Verify review was persisted to database
    # Query the reviews table
    reviews_result = repo.client.table("reviews").select("*").eq("conversation_id", test_conversation["id"]).execute()
    
    assert len(reviews_result.data) > 0, "Review was not persisted to database"
    
    review = reviews_result.data[0]
    
    # Requirement 7.1: Complaint should have negative rating
    assert review["rating"] <= 2, f"Complaint should have rating <= 2, got {review['rating']}"
    
    # Requirement 7.3: Complaint should be marked with requires_attention
    assert review["requires_attention"] is True, "Complaint should have requires_attention = True"
    
    # Requirement 7.4: Review should have comment and source
    assert review["comment"] == complaint_message
    assert review["source"] == "chat"
    
    print(f"✓ Complaint handled correctly: rating={review['rating']}, requires_attention={review['requires_attention']}")


def test_positive_review_handling(test_tenant, repo):
    """Test that positive reviews are properly classified and persisted"""
    # Requirement 7.2: Positive reviews should be classified with appropriate rating
    
    # Create a new conversation for this test
    conversation = repo.create_conversation(
        tenant_id=test_tenant["id"],
        channel="web",
        customer_id="test_customer_2"
    )
    
    positive_message = "¡Excelente servicio! La comida estaba deliciosa, 5 estrellas."
    
    state: AgentState = {
        "tenant_id": test_tenant["id"],
        "conversation_id": conversation["id"],
        "messages": [HumanMessage(content=positive_message)],
        "intent": "review",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Handle the review
    result_state = handle_review(state)
    
    # Verify response is grateful
    assert result_state["final_response"] is not None
    assert "thank" in result_state["final_response"].lower() or "gracias" in result_state["final_response"].lower()
    
    # Verify review was persisted to database
    reviews_result = repo.client.table("reviews").select("*").eq("conversation_id", conversation["id"]).execute()
    
    assert len(reviews_result.data) > 0, "Review was not persisted to database"
    
    review = reviews_result.data[0]
    
    # Requirement 7.2: Positive review should have high rating
    assert review["rating"] >= 4, f"Positive review should have rating >= 4, got {review['rating']}"
    
    # Positive reviews should not require attention
    assert review["requires_attention"] is False, "Positive review should not require attention"
    
    # Requirement 7.4: Review should have comment and source
    assert review["comment"] == positive_message
    assert review["source"] == "chat"
    
    print(f"✓ Positive review handled correctly: rating={review['rating']}, requires_attention={review['requires_attention']}")


def test_neutral_feedback_handling(test_tenant, repo):
    """Test that neutral feedback is handled appropriately"""
    
    # Create a new conversation for this test
    conversation = repo.create_conversation(
        tenant_id=test_tenant["id"],
        channel="web",
        customer_id="test_customer_3"
    )
    
    neutral_message = "La comida estuvo bien, nada especial."
    
    state: AgentState = {
        "tenant_id": test_tenant["id"],
        "conversation_id": conversation["id"],
        "messages": [HumanMessage(content=neutral_message)],
        "intent": "review",
        "context": None,
        "order_draft": None,
        "requires_confirmation": False,
        "final_response": None
    }
    
    # Handle the review
    result_state = handle_review(state)
    
    # Verify response acknowledges feedback
    assert result_state["final_response"] is not None
    assert "feedback" in result_state["final_response"].lower() or "thank" in result_state["final_response"].lower()
    
    # Verify review was persisted to database
    reviews_result = repo.client.table("reviews").select("*").eq("conversation_id", conversation["id"]).execute()
    
    assert len(reviews_result.data) > 0, "Review was not persisted to database"
    
    review = reviews_result.data[0]
    
    # Neutral feedback should have moderate rating
    assert 2 <= review["rating"] <= 4, f"Neutral feedback should have rating 2-4, got {review['rating']}"
    
    # Requirement 7.4: Review should have comment and source
    assert review["comment"] == neutral_message
    assert review["source"] == "chat"
    
    print(f"✓ Neutral feedback handled correctly: rating={review['rating']}, requires_attention={review['requires_attention']}")


def test_rating_extraction_accuracy(test_tenant, repo):
    """Test that ratings are extracted accurately from various messages"""
    # Requirement 7.4: Extract rating from message
    
    test_cases = [
        ("Terrible experience, worst food ever", 1, 2),  # Should be 1-2
        ("Not good, disappointed", 1, 2),  # Should be 1-2
        ("It was okay, nothing special", 2, 4),  # Should be 2-4
        ("Good food, would come again", 4, 5),  # Should be 4-5
        ("Amazing! Best restaurant ever!", 4, 5),  # Should be 4-5
    ]
    
    for message, min_rating, max_rating in test_cases:
        # Create a new conversation for each test
        conversation = repo.create_conversation(
            tenant_id=test_tenant["id"],
            channel="web",
            customer_id="test_customer_rating"
        )
        
        state: AgentState = {
            "tenant_id": test_tenant["id"],
            "conversation_id": conversation["id"],
            "messages": [HumanMessage(content=message)],
            "intent": "review",
            "context": None,
            "order_draft": None,
            "requires_confirmation": False,
            "final_response": None
        }
        
        # Handle the review
        result_state = handle_review(state)
        
        # Verify review was persisted
        reviews_result = repo.client.table("reviews").select("*").eq("conversation_id", conversation["id"]).execute()
        assert len(reviews_result.data) > 0
        
        review = reviews_result.data[0]
        
        # Verify rating is in expected range
        assert min_rating <= review["rating"] <= max_rating, \
            f"Message '{message}' should have rating {min_rating}-{max_rating}, got {review['rating']}"
        
        print(f"✓ Rating extraction correct for: '{message}' -> rating={review['rating']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
