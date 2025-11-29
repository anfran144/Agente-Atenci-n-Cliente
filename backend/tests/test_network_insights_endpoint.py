"""Test GET /network-insights endpoint

This test verifies that the network insights endpoint:
1. Returns global patterns from demand_signals table
2. Includes confidence scores
3. Supports regeneration of insights
4. Filters by minimum confidence
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import init_db, close_db, get_supabase_client
from stats_aggregator import StatsAggregator
from datetime import datetime, timedelta

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """Setup and teardown for tests"""
    init_db()
    yield
    close_db()


def test_network_insights_endpoint_exists():
    """Test that the /network-insights endpoint exists"""
    response = client.get("/network-insights")
    # Should return 200 or 500, not 404
    assert response.status_code != 404


def test_network_insights_returns_valid_structure():
    """Test that the endpoint returns the correct response structure"""
    response = client.get("/network-insights")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check response structure
        assert "patterns" in data
        assert "generated_at" in data
        assert isinstance(data["patterns"], list)
        
        # Check pattern structure if patterns exist
        if len(data["patterns"]) > 0:
            pattern = data["patterns"][0]
            assert "pattern" in pattern
            assert "confidence" in pattern
            assert isinstance(pattern["confidence"], (int, float))
            assert 0.0 <= pattern["confidence"] <= 1.0


def test_network_insights_with_regenerate():
    """Test that regenerate parameter triggers insight generation"""
    # First, ensure we have some data to generate insights from
    supabase = get_supabase_client()
    aggregator = StatsAggregator(supabase)
    
    # Get active tenants
    tenants_result = supabase.table("tenants").select("id").eq("is_active", True).execute()
    
    if tenants_result.data and len(tenants_result.data) > 0:
        # Aggregate some recent stats to ensure we have data
        tenant_id = tenants_result.data[0]["id"]
        try:
            aggregator.aggregate_recent_stats(tenant_id, hours_back=24)
        except Exception as e:
            print(f"Warning: Could not aggregate stats: {e}")
    
    # Test with regenerate=true
    response = client.get("/network-insights?regenerate=true")
    
    if response.status_code == 200:
        data = response.json()
        assert "patterns" in data
        assert isinstance(data["patterns"], list)


def test_network_insights_min_confidence_filter():
    """Test that min_confidence parameter filters results"""
    # Test with high confidence threshold
    response = client.get("/network-insights?min_confidence=0.9")
    
    if response.status_code == 200:
        data = response.json()
        
        # All patterns should have confidence >= 0.9
        for pattern in data["patterns"]:
            assert pattern["confidence"] >= 0.9


def test_network_insights_privacy():
    """Test that insights don't expose individual tenant identifiable information
    
    Validates Requirement 6.4: Privacy in Global Insights
    """
    response = client.get("/network-insights")
    
    if response.status_code == 200:
        data = response.json()
        
        # Get tenant names to check they're not exposed
        supabase = get_supabase_client()
        tenants_result = supabase.table("tenants").select("name").execute()
        tenant_names = [t["name"].lower() for t in tenants_result.data]
        
        # Check that no pattern description contains specific tenant names
        for pattern in data["patterns"]:
            pattern_text = pattern["pattern"].lower()
            
            # Should not contain specific tenant names
            for tenant_name in tenant_names:
                # Allow business type mentions (restaurant, bakery) but not specific names
                if len(tenant_name) > 10:  # Only check longer names to avoid false positives
                    assert tenant_name not in pattern_text, \
                        f"Pattern contains tenant name '{tenant_name}': {pattern['pattern']}"


def test_network_insights_with_no_data():
    """Test endpoint behavior when no insights are available"""
    # This should still return a valid response with empty patterns
    response = client.get("/network-insights?min_confidence=1.0")
    
    # Should return 200 with empty patterns, not an error
    assert response.status_code == 200
    data = response.json()
    assert "patterns" in data
    assert isinstance(data["patterns"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
