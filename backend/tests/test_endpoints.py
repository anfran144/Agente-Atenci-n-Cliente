"""Test script to verify API endpoints"""
import httpx
import time
import subprocess
import sys
from pathlib import Path

def test_endpoints():
    """Test API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing API endpoints...")
    
    try:
        # Test root endpoint
        response = httpx.get(f"{base_url}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ GET / - {data}")
        
        # Test health endpoint
        response = httpx.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ GET /health - {data}")
        
        # Test tenants endpoint
        response = httpx.get(f"{base_url}/tenants")
        assert response.status_code == 200
        tenants = response.json()
        assert isinstance(tenants, list)
        assert len(tenants) > 0
        print(f"✓ GET /tenants - Found {len(tenants)} tenants")
        print(f"  Sample tenant: {tenants[0]['name']} ({tenants[0]['type']})")
        
        # Verify tenant response structure
        tenant = tenants[0]
        assert "id" in tenant
        assert "name" in tenant
        assert "type" in tenant
        assert "is_active" in tenant
        print("✓ Tenant response structure validated")
        
        print("\n" + "=" * 60)
        print("✓ ALL ENDPOINT TESTS PASSED")
        print("=" * 60)
        
    except httpx.ConnectError:
        print("✗ Could not connect to server. Make sure it's running on port 8000")
        return 1
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    print("=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)
    print("\nNote: Server must be running on http://localhost:8000")
    print("Start server with: uvicorn main:app --reload")
    print()
    
    exit(test_endpoints())
