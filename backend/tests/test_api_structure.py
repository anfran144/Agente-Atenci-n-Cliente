"""Test script to verify core backend API structure"""
import pytest
from database import init_db, get_supabase_client
from repository import Repository
from models import ChatRequest, ChatResponse, TenantResponse, StatsResponse

@pytest.fixture
def client():
    """Fixture to provide database client"""
    return init_db()

@pytest.fixture
def repo(client):
    """Fixture to provide repository instance"""
    return Repository(client)

@pytest.fixture
def tenant_id(repo):
    """Fixture to provide a valid tenant_id"""
    tenants = repo.get_active_tenants()
    if tenants:
        return tenants[0]['id']
    pytest.skip("No active tenants available")

def test_database_connection(client):
    """Test database initialization and connection"""
    print("Testing database connection...")
    assert client is not None, "Database client should be initialized"
    print("✓ Database connection successful")

def test_repository_tenant_operations(repo):
    """Test repository tenant operations with tenant_id filtering"""
    print("\nTesting repository tenant operations...")
    
    # Test get active tenants
    tenants = repo.get_active_tenants()
    print(f"✓ Found {len(tenants)} active tenants")
    
    if tenants:
        tenant = tenants[0]
        print(f"✓ Sample tenant: {tenant['name']} ({tenant['type']})")
        
        # Test get specific tenant
        tenant_data = repo.get_tenant(tenant['id'])
        assert tenant_data is not None, "Should retrieve tenant by ID"
        print(f"✓ Retrieved tenant by ID: {tenant_data['name']}")
        
        # Test tenant-filtered queries
        products = repo.get_products(tenant['id'])
        print(f"✓ Found {len(products)} products for tenant {tenant['name']}")
        
        faqs = repo.get_faqs(tenant['id'])
        print(f"✓ Found {len(faqs)} FAQs for tenant {tenant['name']}")
        
        # Verify tenant_id filtering
        for product in products:
            assert product['tenant_id'] == tenant['id'], "Product should belong to correct tenant"
        print("✓ Tenant ID filtering verified for products")
        
        for faq in faqs:
            assert faq['tenant_id'] == tenant['id'], "FAQ should belong to correct tenant"
        print("✓ Tenant ID filtering verified for FAQs")

def test_pydantic_models():
    """Test Pydantic model validation"""
    print("\nTesting Pydantic models...")
    
    # Test ChatRequest
    chat_req = ChatRequest(
        tenant_id="test-tenant",
        message="Hello",
        customer_id="customer-123"
    )
    assert chat_req.tenant_id == "test-tenant"
    print("✓ ChatRequest model validated")
    
    # Test TenantResponse
    tenant_resp = TenantResponse(
        id="tenant-1",
        name="Test Restaurant",
        type="restaurant",
        is_active=True
    )
    assert tenant_resp.name == "Test Restaurant"
    print("✓ TenantResponse model validated")
    
    print("✓ All Pydantic models validated successfully")

def test_repository_conversation_operations(repo, tenant_id):
    """Test conversation and message operations"""
    print("\nTesting conversation operations...")
    
    # Create a test conversation
    conversation = repo.create_conversation(
        tenant_id=tenant_id,
        channel="web",
        customer_id="test-customer"
    )
    assert conversation['tenant_id'] == tenant_id, "Conversation should have correct tenant_id"
    print(f"✓ Created conversation: {conversation['id']}")
    
    # Create a test message
    message = repo.create_message(
        conversation_id=conversation['id'],
        sender="user",
        text="Test message",
        intent="faq"
    )
    assert message['conversation_id'] == conversation['id']
    print(f"✓ Created message: {message['id']}")
    
    # Retrieve messages
    messages = repo.get_messages(conversation['id'])
    assert len(messages) > 0, "Should retrieve created message"
    print(f"✓ Retrieved {len(messages)} message(s)")
    
    # End conversation
    ended = repo.end_conversation(conversation['id'])
    assert ended['ended_at'] is not None, "Conversation should have ended_at timestamp"
    print("✓ Ended conversation successfully")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Core Backend API Structure")
    print("=" * 60)
    
    try:
        # Test 1: Database connection
        client = test_database_connection()
        
        # Test 2: Repository initialization
        repo = Repository(client)
        print("\n✓ Repository initialized successfully")
        
        # Test 3: Tenant operations
        test_repository_tenant_operations(repo)
        
        # Test 4: Pydantic models
        test_pydantic_models()
        
        # Test 5: Conversation operations (if we have tenants)
        tenants = repo.get_active_tenants()
        if tenants:
            test_repository_conversation_operations(repo, tenants[0]['id'])
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
