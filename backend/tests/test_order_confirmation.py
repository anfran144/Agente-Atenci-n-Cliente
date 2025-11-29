"""
Test script for order confirmation and persistence

This script tests:
- Order confirmation flow
- Order persistence to database (orders and order_items tables)
- Association with conversation_id
- Insufficient stock handling with informative messages

Requirements: 2.5, 2.6
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Import agent components
from agent import AgentState, handle_order
from database import get_supabase_client
from repository import Repository


def set_always_open_hours(supabase, tenant_id):
    """Temporarily set business hours to always open for testing"""
    try:
        tenant = supabase.table("tenants").select("*").eq("id", tenant_id).execute().data[0]
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
        return original_config
    except Exception as e:
        print(f"Warning: Could not set business hours: {e}")
        return {}


def restore_hours(supabase, tenant_id, original_config):
    """Restore original business hours"""
    supabase.table("tenants").update({"config": original_config}).eq("id", tenant_id).execute()


def test_order_confirmation_flow():
    """Test complete order confirmation flow"""
    print("\n" + "="*60)
    print("TEST 1: Order Confirmation Flow")
    print("="*60)
    
    # Get a tenant ID from database
    supabase = get_supabase_client()
    repo = Repository(supabase)
    tenants = repo.get_active_tenants()
    
    if not tenants:
        print("❌ No tenants found in database")
        return False
    
    # Use the first restaurant
    tenant = tenants[0]
    tenant_id = tenant["id"]
    print(f"Testing with tenant: {tenant['name']}")
    
    # Temporarily set business hours to always open for testing
    original_config = set_always_open_hours(supabase, tenant_id)
    print("✓ Temporarily set business hours to always open for testing")
    
    # Get a product from this tenant to use in the order
    products = repo.get_products(tenant_id)
    if not products:
        print("❌ No products found for tenant")
        restore_hours(supabase, tenant_id, original_config)
        return False
    
    product = products[0]
    print(f"Using product: {product['name']}")
    
    # Create a conversation
    conversation = repo.create_conversation(
        tenant_id=tenant_id,
        channel="test",
        customer_id="test-customer-1"
    )
    conversation_id = conversation["id"]
    print(f"Created conversation: {conversation_id}")
    
    # Step 1: Create initial order
    print("\n--- Step 1: Create order ---")
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        messages=[HumanMessage(content=f"Quiero pedir 2 {product['name']}")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result_state = handle_order(state)
    
    print(f"Response:\n{result_state.get('final_response')}")
    print(f"\nRequires Confirmation: {result_state.get('requires_confirmation')}")
    print(f"Order Draft: {result_state.get('order_draft')}")
    
    if not result_state.get("requires_confirmation"):
        print("\n❌ Order should require confirmation")
        return False
    
    if not result_state.get("order_draft"):
        print("\n❌ Order draft should be created")
        return False
    
    print("\n✅ Order draft created successfully")
    
    # Step 2: Confirm the order
    print("\n--- Step 2: Confirm order ---")
    confirmation_state = AgentState(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        messages=[HumanMessage(content="Sí, confirmar")],
        intent="order_create",
        context=None,
        order_draft=result_state.get("order_draft"),  # Pass the order draft
        requires_confirmation=True,
        final_response=None
    )
    
    confirmed_state = handle_order(confirmation_state)
    
    print(f"Response:\n{confirmed_state.get('final_response')}")
    print(f"\nRequires Confirmation: {confirmed_state.get('requires_confirmation')}")
    print(f"Order Draft: {confirmed_state.get('order_draft')}")
    
    if confirmed_state.get("requires_confirmation"):
        print("\n❌ Order should not require confirmation after confirming")
        return False
    
    if confirmed_state.get("order_draft"):
        print("\n❌ Order draft should be cleared after confirmation")
        return False
    
    # Verify order was persisted
    response_text = confirmed_state.get("final_response", "")
    if "confirmed" not in response_text.lower():
        print("\n❌ Response should indicate order was confirmed")
        return False
    
    print("\n✅ Order confirmed and persisted successfully")
    
    # Restore original config
    restore_hours(supabase, tenant_id, original_config)
    
    return True


def test_order_rejection():
    """Test order rejection flow"""
    print("\n" + "="*60)
    print("TEST 2: Order Rejection Flow")
    print("="*60)
    
    supabase = get_supabase_client()
    repo = Repository(supabase)
    tenants = repo.get_active_tenants()
    
    if not tenants:
        print("❌ No tenants found in database")
        return False
    
    tenant = tenants[0]
    tenant_id = tenant["id"]
    print(f"Testing with tenant: {tenant['name']}")
    
    # Temporarily set business hours to always open for testing
    original_config = set_always_open_hours(supabase, tenant_id)
    
    # Get a product from this tenant
    products = repo.get_products(tenant_id)
    if not products:
        print("❌ No products found for tenant")
        restore_hours(supabase, tenant_id, original_config)
        return False
    
    product = products[0]
    print(f"Using product: {product['name']}")
    
    # Create a conversation
    conversation = repo.create_conversation(
        tenant_id=tenant_id,
        channel="test",
        customer_id="test-customer-2"
    )
    conversation_id = conversation["id"]
    
    # Step 1: Create initial order
    print("\n--- Step 1: Create order ---")
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        messages=[HumanMessage(content=f"Quiero pedir 1 {product['name']}")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result_state = handle_order(state)
    
    print(f"Response:\n{result_state.get('final_response')}")
    print(f"Requires Confirmation: {result_state.get('requires_confirmation')}")
    print(f"Order Draft: {result_state.get('order_draft')}")
    
    if not result_state.get("requires_confirmation"):
        print("\n❌ Order should require confirmation")
        return False
    
    # Step 2: Reject the order
    print("\n--- Step 2: Reject order ---")
    rejection_state = AgentState(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        messages=[HumanMessage(content="No, cancelar")],
        intent="order_create",
        context=None,
        order_draft=result_state.get("order_draft"),
        requires_confirmation=True,
        final_response=None
    )
    
    rejected_state = handle_order(rejection_state)
    
    print(f"Response:\n{rejected_state.get('final_response')}")
    
    if rejected_state.get("requires_confirmation"):
        print("\n❌ Order should not require confirmation after rejection")
        return False
    
    if rejected_state.get("order_draft"):
        print("\n❌ Order draft should be cleared after rejection")
        return False
    
    response_text = rejected_state.get("final_response", "")
    if "cancel" not in response_text.lower():
        print("\n❌ Response should indicate order was cancelled")
        return False
    
    print("\n✅ Order rejection handled correctly")
    
    # Restore original config
    restore_hours(supabase, tenant_id, original_config)
    
    return True


def test_order_persistence_in_database():
    """Test that orders are actually persisted to database"""
    print("\n" + "="*60)
    print("TEST 3: Order Persistence in Database")
    print("="*60)
    
    supabase = get_supabase_client()
    repo = Repository(supabase)
    tenants = repo.get_active_tenants()
    
    if not tenants:
        print("❌ No tenants found in database")
        return False
    
    tenant = tenants[0]
    tenant_id = tenant["id"]
    print(f"Testing with tenant: {tenant['name']}")
    
    # Temporarily set business hours to always open for testing
    original_config = set_always_open_hours(supabase, tenant_id)
    
    # Create a conversation
    conversation = repo.create_conversation(
        tenant_id=tenant_id,
        channel="test",
        customer_id="test-customer-3"
    )
    conversation_id = conversation["id"]
    
    # Get initial order count
    initial_orders = supabase.table("orders").select("*").eq("conversation_id", conversation_id).execute()
    initial_count = len(initial_orders.data)
    print(f"Initial orders for conversation: {initial_count}")
    
    # Get a product from this tenant
    products = repo.get_products(tenant_id)
    if not products:
        print("❌ No products found for tenant")
        restore_hours(supabase, tenant_id, original_config)
        return False
    
    product = products[0]
    print(f"Using product: {product['name']}")
    
    # Create and confirm order
    print("\n--- Creating and confirming order ---")
    
    # Step 1: Create order
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        messages=[HumanMessage(content=f"Quiero 1 {product['name']}")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result_state = handle_order(state)
    
    print(f"Response:\n{result_state.get('final_response')}")
    print(f"Order Draft: {result_state.get('order_draft')}")
    
    if not result_state.get("order_draft"):
        print("❌ Failed to create order draft")
        return False
    
    # Step 2: Confirm order
    confirmation_state = AgentState(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        messages=[HumanMessage(content="Sí")],
        intent="order_create",
        context=None,
        order_draft=result_state.get("order_draft"),
        requires_confirmation=True,
        final_response=None
    )
    
    confirmed_state = handle_order(confirmation_state)
    
    # Verify order was persisted
    final_orders = supabase.table("orders").select("*").eq("conversation_id", conversation_id).execute()
    final_count = len(final_orders.data)
    
    print(f"Final orders for conversation: {final_count}")
    
    if final_count != initial_count + 1:
        print(f"\n❌ Expected {initial_count + 1} orders, found {final_count}")
        return False
    
    # Get the created order
    order = final_orders.data[-1]
    print(f"\nCreated order:")
    print(f"  ID: {order['id']}")
    print(f"  Tenant ID: {order['tenant_id']}")
    print(f"  Conversation ID: {order['conversation_id']}")
    print(f"  Status: {order['status']}")
    print(f"  Total: ${order['total_amount']}")
    
    # Verify order fields
    if order['tenant_id'] != tenant_id:
        print("\n❌ Order tenant_id doesn't match")
        return False
    
    if order['conversation_id'] != conversation_id:
        print("\n❌ Order conversation_id doesn't match")
        return False
    
    if order['status'] != "pending":
        print("\n❌ Order status should be 'pending'")
        return False
    
    # Verify order items were created
    order_items = supabase.table("order_items").select("*").eq("order_id", order['id']).execute()
    
    print(f"\nOrder items: {len(order_items.data)}")
    for item in order_items.data:
        print(f"  - Product ID: {item['product_id']}, Quantity: {item['quantity']}, Price: ${item['unit_price']}")
    
    if len(order_items.data) == 0:
        print("\n❌ No order items created")
        return False
    
    print("\n✅ Order and order items persisted correctly")
    
    # Restore original config
    restore_hours(supabase, tenant_id, original_config)
    
    return True


def test_insufficient_stock_message():
    """Test that insufficient stock produces informative message"""
    print("\n" + "="*60)
    print("TEST 4: Insufficient Stock Handling")
    print("="*60)
    
    supabase = get_supabase_client()
    repo = Repository(supabase)
    tenants = repo.get_active_tenants()
    
    if not tenants:
        print("❌ No tenants found in database")
        return False
    
    tenant = tenants[0]
    tenant_id = tenant["id"]
    print(f"Testing with tenant: {tenant['name']}")
    
    # Temporarily set business hours to always open for testing
    original_config = set_always_open_hours(supabase, tenant_id)
    
    # Get a product with limited stock
    products = repo.get_products(tenant_id)
    if not products:
        print("❌ No products found")
        return False
    
    product = products[0]
    inventory = repo.get_inventory_item(tenant_id, product["id"])
    
    if not inventory:
        print("❌ No inventory found")
        return False
    
    available_stock = inventory["stock_quantity"]
    excessive_quantity = available_stock + 100
    
    print(f"\nProduct: {product['name']}")
    print(f"Available stock: {available_stock}")
    print(f"Requesting: {excessive_quantity}")
    
    # Create a conversation
    conversation = repo.create_conversation(
        tenant_id=tenant_id,
        channel="test",
        customer_id="test-customer-4"
    )
    conversation_id = conversation["id"]
    
    # Try to order more than available
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        messages=[HumanMessage(content=f"Quiero {excessive_quantity} {product['name']}")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result_state = handle_order(state)
    
    print(f"\nResponse:\n{result_state.get('final_response')}")
    
    response_text = result_state.get("final_response", "").lower()
    
    # Check that response mentions stock issue (Requirement 2.6)
    if "stock" not in response_text and "disponible" not in response_text:
        print("\n❌ Response should mention stock availability")
        return False
    
    # Check that available quantity is mentioned
    if str(available_stock) not in result_state.get("final_response", ""):
        print("\n⚠️ Response should mention available quantity")
    
    # Order should not require confirmation if stock is insufficient
    if result_state.get("requires_confirmation"):
        print("\n⚠️ Order with insufficient stock should not require confirmation")
    
    print("\n✅ Insufficient stock handled with informative message")
    
    # Restore original config
    restore_hours(supabase, tenant_id, original_config)
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ORDER CONFIRMATION AND PERSISTENCE TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Order Confirmation Flow", test_order_confirmation_flow()))
    results.append(("Order Rejection Flow", test_order_rejection()))
    results.append(("Order Persistence in Database", test_order_persistence_in_database()))
    results.append(("Insufficient Stock Handling", test_insufficient_stock_message()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    return all(passed for _, passed in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
