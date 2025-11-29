"""
Test for GET /tenants endpoint

This test verifies:
- Endpoint returns list of active tenants
- Response matches TenantResponse model
- Only active tenants are returned
- Requirement 9.1: Display available tenants for selection
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import init_db, close_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """Setup and teardown for tests"""
    init_db()
    yield
    close_db()

def test_get_tenants_endpoint_exists():
    """Test that /tenants endpoint exists and returns 200"""
    response = client.get("/tenants")
    assert response.status_code == 200

def test_get_tenants_returns_list():
    """Test that /tenants returns a list"""
    response = client.get("/tenants")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_tenants_response_structure():
    """Test that each tenant has required fields"""
    response = client.get("/tenants")
    assert response.status_code == 200
    tenants = response.json()
    
    # Should have at least one tenant (we seeded 5)
    assert len(tenants) > 0
    
    # Check structure of first tenant
    tenant = tenants[0]
    assert "id" in tenant
    assert "name" in tenant
    assert "type" in tenant
    assert "is_active" in tenant
    
    # Verify types
    assert isinstance(tenant["id"], str)
    assert isinstance(tenant["name"], str)
    assert isinstance(tenant["type"], str)
    assert isinstance(tenant["is_active"], bool)

def test_get_tenants_only_active():
    """Test that only active tenants are returned (Requirement 9.1)"""
    response = client.get("/tenants")
    assert response.status_code == 200
    tenants = response.json()
    
    # All returned tenants should be active
    for tenant in tenants:
        assert tenant["is_active"] is True

def test_get_tenants_has_expected_count():
    """Test that we have at least the minimum expected tenants"""
    response = client.get("/tenants")
    assert response.status_code == 200
    tenants = response.json()
    
    # We should have at least 5 tenants (3 restaurants, 1 bakery, 1 minimarket)
    assert len(tenants) >= 5

def test_get_tenants_has_expected_types():
    """Test that tenants have expected business types"""
    response = client.get("/tenants")
    assert response.status_code == 200
    tenants = response.json()
    
    # Extract types
    types = [t["type"] for t in tenants]
    
    # Should have restaurants, bakery, and minimarket
    assert "restaurant" in types
    assert "bakery" in types
    assert "minimarket" in types
    
    # Count types - should have at least the minimum
    assert types.count("restaurant") >= 3
    assert types.count("bakery") >= 1
    assert types.count("minimarket") >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
