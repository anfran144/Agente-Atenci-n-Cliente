"""
Integration test for complete order flow through /chat endpoint

This test verifies the end-to-end order confirmation flow:
1. User sends order request via /chat
2. Agent responds with order summary
3. User confirms via /chat
4. Order is persisted to database
"""

import requests
from database import get_supabase_client
from repository import Repository

BASE_URL = "http://localhost:8000"

def test_order_flow_via_chat_endpoint():
    """Test complete order flow through the chat endpoint"""
    print("\n" + "="*60)
    print("ORDER FLOW INTEGRATION TEST (via /chat endpoint)")
    print("="*60)
    
    # Initialize
    supabase = get_supabase_client()
    repo = Repository(supabase)
    
    # Get a tenant
    tenants = repo.get_active_tenants()
    if not tenants:
        print("❌ No tenants found")
        return False
    
    tenant = tenants[0]
    tenant_id = tenant["id"]
    print(f"\n✓ Using tenant: {tenant['name']}")
    
    # Temporarily set business hours to always open
    original_config = tenant.get("config", {})
    test_config = original_config.copy()
    test_config["business_hours"] = {
        "monday": "00:00-23:59",
        "tuesday": "00:00-23:59",
        "wednesday": "00:00-23:59",
        "thursday": "00:00-23:59",
        "friday": "00:00-23:59",
        "saturday": "00:00-23:59",
        "sunday": "00:00-23:59"
    }
    supabase.table("tenants").update({"config": test_config}).eq("id", tenant_id).execute()
    
    # Get a product
    products = repo.get_products(tenant_id)
    if not products:
        print("❌ No products found")
        supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
        return False
    
    product = products[0]
    print(f"✓ Using product: {product['name']}")
    
    try:
        # Step 1: Send order request
        print("\n" + "-"*60)
        print("STEP 1: Send order request via /chat")
        print("-"*60)
        
        order_request = {
            "tenant_id": tenant_id,
            "message": f"Quiero pedir 2 {product['name']}",
            "customer_id": "integration-test-user"
        }
        
        print(f"POST /chat")
        print(f"Request: {order_request}")
        
        response1 = requests.post(f"{BASE_URL}/chat", json=order_request)
        
        if response1.status_code != 200:
            print(f"\n❌ Request failed with status {response1.status_code}")
            print(f"Response: {response1.text}")
            supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
            return False
        
        data1 = response1.json()
        conversation_id = data1["conversation_id"]
        
        print(f"\n✓ Response received:")
        print(f"  - Conversation ID: {conversation_id}")
        print(f"  - Intent: {data1['intent']}")
        print(f"  - Requires Confirmation: {data1['requires_confirmation']}")
        print(f"\nAgent: {data1['response']}")
        
        if not data1['requires_confirmation']:
            print("\n❌ Order should require confirmation")
            supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
            return False
        
        # Step 2: Send confirmation
        print("\n" + "-"*60)
        print("STEP 2: Send confirmation via /chat")
        print("-"*60)
        
        confirmation_request = {
            "tenant_id": tenant_id,
            "conversation_id": conversation_id,
            "message": "Sí, confirmar",
            "customer_id": "integration-test-user"
        }
        
        print(f"POST /chat")
        print(f"Request: {confirmation_request}")
        
        response2 = requests.post(f"{BASE_URL}/chat", json=confirmation_request)
        
        if response2.status_code != 200:
            print(f"\n❌ Request failed with status {response2.status_code}")
            print(f"Response: {response2.text}")
            supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
            return False
        
        data2 = response2.json()
        
        print(f"\n✓ Response received:")
        print(f"  - Intent: {data2['intent']}")
        print(f"  - Requires Confirmation: {data2['requires_confirmation']}")
        print(f"\nAgent: {data2['response']}")
        
        if "confirmed" not in data2['response'].lower():
            print("\n❌ Response should indicate order was confirmed")
            supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
            return False
        
        # Step 3: Verify database
        print("\n" + "-"*60)
        print("STEP 3: Verify order in database")
        print("-"*60)
        
        orders = supabase.table("orders").select("*").eq("conversation_id", conversation_id).execute()
        
        if not orders.data:
            print("\n❌ No orders found in database")
            supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
            return False
        
        order = orders.data[0]
        print(f"\n✓ Order found in database:")
        print(f"  - Order ID: {order['id']}")
        print(f"  - Status: {order['status']}")
        print(f"  - Total: ${order['total_amount']}")
        
        # Get order items
        order_items = supabase.table("order_items").select("*").eq("order_id", order['id']).execute()
        print(f"  - Order items: {len(order_items.data)}")
        
        # Verify
        if order['status'] != 'pending':
            print("\n❌ Order status should be 'pending'")
            supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
            return False
        
        if len(order_items.data) == 0:
            print("\n❌ Order should have items")
            supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
            return False
        
        print("\n" + "="*60)
        print("✅ INTEGRATION TEST PASSED")
        print("="*60)
        
        supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Make sure the server is running:")
        print("   cd backend && uvicorn main:app --reload")
        supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
        return False
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()
        return False

if __name__ == "__main__":
    success = test_order_flow_via_chat_endpoint()
    exit(0 if success else 1)
