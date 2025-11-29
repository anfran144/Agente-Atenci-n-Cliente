"""Tests for GET /stats/{tenant_id} endpoint

Requirements tested:
- 5.1: Peak hours calculation from tenant_stats
- 5.2: Top products by counting mentions in messages
- 5.3: Common questions identification
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_supabase_client
from repository import Repository
from datetime import datetime, date, timedelta
import uuid

client = TestClient(app)


@pytest.fixture
def setup_test_data():
    """Setup test data for stats endpoint testing"""
    supabase = get_supabase_client()
    repo = Repository(supabase)
    
    # Get an existing tenant (should be seeded)
    tenants = repo.get_active_tenants()
    if not tenants:
        pytest.skip("No tenants available for testing")
    
    tenant_id = tenants[0]["id"]
    
    # Create a test conversation
    conversation = repo.create_conversation(
        tenant_id=tenant_id,
        channel="web",
        customer_id="test_customer"
    )
    conversation_id = conversation["id"]
    
    # Create test messages with different intents
    messages = [
        {"text": "What are your hours?", "intent": "faq"},
        {"text": "I want to order pizza", "intent": "order_create"},
        {"text": "Do you have pasta?", "intent": "faq"},
        {"text": "What time do you close?", "intent": "faq"},
        {"text": "I'd like to order a burger", "intent": "order_create"},
    ]
    
    for msg in messages:
        repo.create_message(
            conversation_id=conversation_id,
            sender="user",
            text=msg["text"],
            intent=msg["intent"]
        )
    
    # Create some tenant_stats entries
    from stats_aggregator import StatsAggregator
    aggregator = StatsAggregator(supabase)
    
    # Aggregate stats for the last few hours
    now = datetime.utcnow()
    for i in range(5):
        target_time = now - timedelta(hours=i)
        try:
            aggregator.aggregate_tenant_stats(
                tenant_id=tenant_id,
                target_date=target_time.date(),
                hour=target_time.hour
            )
        except Exception as e:
            print(f"Warning: Could not aggregate stats: {e}")
    
    yield {
        "tenant_id": tenant_id,
        "conversation_id": conversation_id
    }
    
    # Cleanup is handled by database cascade deletes


def test_stats_endpoint_exists():
    """Test that the stats endpoint exists and returns 404 for invalid tenant"""
    response = client.get("/stats/invalid-tenant-id")
    assert response.status_code in [404, 500]  # Either not found or invalid UUID


def test_stats_endpoint_returns_correct_structure(setup_test_data):
    """Test that stats endpoint returns correct response structure"""
    tenant_id = setup_test_data["tenant_id"]
    
    response = client.get(f"/stats/{tenant_id}")
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify response structure
    assert "tenant_id" in data
    assert "peak_hours" in data
    assert "top_products" in data
    assert "common_questions" in data
    
    assert data["tenant_id"] == tenant_id
    
    # Verify peak_hours structure
    assert isinstance(data["peak_hours"], list)
    for hour_stat in data["peak_hours"]:
        assert "hour" in hour_stat
        assert "count" in hour_stat
        assert 0 <= hour_stat["hour"] <= 23
        assert hour_stat["count"] >= 0
    
    # Verify top_products structure
    assert isinstance(data["top_products"], list)
    for product_stat in data["top_products"]:
        assert "product_id" in product_stat
        assert "name" in product_stat
        assert "mentions" in product_stat
        assert product_stat["mentions"] >= 0
    
    # Verify common_questions structure
    assert isinstance(data["common_questions"], list)
    for question in data["common_questions"]:
        assert "question" in question
        assert "frequency" in question
        assert question["frequency"] >= 0


def test_peak_hours_ordered_by_count(setup_test_data):
    """Test that peak hours are ordered by interaction count (Requirement 5.1)"""
    tenant_id = setup_test_data["tenant_id"]
    
    response = client.get(f"/stats/{tenant_id}")
    assert response.status_code == 200
    
    data = response.json()
    peak_hours = data["peak_hours"]
    
    # Verify ordering: each count should be >= the next
    for i in range(len(peak_hours) - 1):
        assert peak_hours[i]["count"] >= peak_hours[i + 1]["count"], \
            "Peak hours should be ordered by count descending"


def test_top_products_from_messages(setup_test_data):
    """Test that top products are calculated from message mentions (Requirement 5.2)"""
    tenant_id = setup_test_data["tenant_id"]
    
    response = client.get(f"/stats/{tenant_id}")
    assert response.status_code == 200
    
    data = response.json()
    top_products = data["top_products"]
    
    # Verify ordering: each mention count should be >= the next
    for i in range(len(top_products) - 1):
        assert top_products[i]["mentions"] >= top_products[i + 1]["mentions"], \
            "Top products should be ordered by mentions descending"


def test_common_questions_identified(setup_test_data):
    """Test that common questions are identified from messages (Requirement 5.3)"""
    tenant_id = setup_test_data["tenant_id"]
    
    response = client.get(f"/stats/{tenant_id}")
    assert response.status_code == 200
    
    data = response.json()
    common_questions = data["common_questions"]
    
    # Verify ordering: each frequency should be >= the next
    for i in range(len(common_questions) - 1):
        assert common_questions[i]["frequency"] >= common_questions[i + 1]["frequency"], \
            "Common questions should be ordered by frequency descending"
    
    # Verify questions end with '?'
    for question in common_questions:
        assert question["question"].endswith("?"), \
            "Common questions should be actual questions ending with '?'"


def test_stats_tenant_isolation(setup_test_data):
    """Test that stats are isolated by tenant_id"""
    tenant_id = setup_test_data["tenant_id"]
    
    # Get stats for this tenant
    response1 = client.get(f"/stats/{tenant_id}")
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Get all tenants
    supabase = get_supabase_client()
    repo = Repository(supabase)
    tenants = repo.get_active_tenants()
    
    if len(tenants) > 1:
        # Get stats for a different tenant
        other_tenant_id = next(t["id"] for t in tenants if t["id"] != tenant_id)
        response2 = client.get(f"/stats/{other_tenant_id}")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify tenant_ids are different
        assert data1["tenant_id"] != data2["tenant_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
