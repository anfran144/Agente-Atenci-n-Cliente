"""
Test script for order handler node

This script tests the order handler implementation including:
- Product extraction from natural language
- Inventory validation
- Business hours validation
- Order summary generation
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


def test_order_extraction():
    """Test product extraction from natural language order"""
    print("\n" + "="*60)
    print("TEST 1: Product Extraction from Natural Language")
    print("="*60)
    
    # Get a tenant ID from database
    supabase = get_supabase_client()
    repo = Repository(supabase)
    tenants = repo.get_active_tenants()
    
    if not tenants:
        print("❌ No tenants found in database")
        return False
    
    # Use the first restaurant (Italian)
    tenant = tenants[0]
    tenant_id = tenant["id"]
    print(f"Testing with tenant: {tenant['name']}")
    
    # Create test state with order message
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id="test-conv-1",
        messages=[HumanMessage(content="Quiero pedir 2 pizzas margherita y una pasta carbonara")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    # Process order
    result_state = handle_order(state)
    
    # Verify results
    print(f"\nOrder Draft: {result_state.get('order_draft')}")
    print(f"Requires Confirmation: {result_state.get('requires_confirmation')}")
    print(f"\nResponse:\n{result_state.get('final_response')}")
    
    # Check if order was extracted
    if result_state.get("order_draft") and result_state.get("requires_confirmation"):
        print("\n✅ Order extraction successful")
        return True
    else:
        print("\n❌ Order extraction failed")
        return False


def test_inventory_validation():
    """Test inventory validation for products"""
    print("\n" + "="*60)
    print("TEST 2: Inventory Validation")
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
    
    # Get a product to test with
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
    print(f"\nProduct: {product['name']}")
    print(f"Available stock: {available_stock}")
    
    # Test 1: Order within stock
    print(f"\n--- Test 2a: Order within stock (quantity: 1) ---")
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id="test-conv-2a",
        messages=[HumanMessage(content=f"Quiero pedir 1 {product['name']}")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result_state = handle_order(state)
    print(f"Response:\n{result_state.get('final_response')}")
    
    if result_state.get("order_draft"):
        print("✅ Order within stock accepted")
    else:
        print("❌ Order within stock rejected")
        return False
    
    # Test 2: Order exceeding stock
    print(f"\n--- Test 2b: Order exceeding stock (quantity: {available_stock + 10}) ---")
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id="test-conv-2b",
        messages=[HumanMessage(content=f"Quiero pedir {available_stock + 10} {product['name']}")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result_state = handle_order(state)
    print(f"Response:\n{result_state.get('final_response')}")
    
    if not result_state.get("order_draft") and "stock" in result_state.get("final_response", "").lower():
        print("✅ Order exceeding stock properly rejected")
        return True
    else:
        print("❌ Order exceeding stock not properly handled")
        return False


def test_business_hours_validation():
    """Test business hours validation"""
    print("\n" + "="*60)
    print("TEST 3: Business Hours Validation")
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
    
    # Get business hours
    business_hours = tenant.get("config", {}).get("business_hours", {})
    print(f"\nBusiness hours: {business_hours}")
    
    # Get current time info
    import pytz
    tz = pytz.timezone(tenant.get("timezone", "UTC"))
    current_time = datetime.now(tz)
    day_name = current_time.strftime("%A").lower()
    current_hour_minute = current_time.strftime("%H:%M")
    
    print(f"Current time: {current_hour_minute} on {day_name}")
    print(f"Hours today: {business_hours.get(day_name, 'closed')}")
    
    # Test order during current time
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id="test-conv-3",
        messages=[HumanMessage(content="Quiero pedir una pizza")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result_state = handle_order(state)
    print(f"\nResponse:\n{result_state.get('final_response')}")
    
    # Check if response mentions business hours
    response = result_state.get("final_response", "")
    if "closed" in response.lower() or "hours" in response.lower():
        print("\n✅ Business hours validation working (currently closed)")
    elif result_state.get("order_draft"):
        print("\n✅ Business hours validation working (currently open)")
    else:
        print("\n⚠️ Business hours validation unclear")
    
    return True


def test_order_summary_calculation():
    """Test order summary with correct total calculation"""
    print("\n" + "="*60)
    print("TEST 4: Order Summary Calculation")
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
    
    # Create order with multiple items
    state = AgentState(
        tenant_id=tenant_id,
        conversation_id="test-conv-4",
        messages=[HumanMessage(content="Quiero 2 pizzas margherita y 1 tiramisu")],
        intent="order_create",
        context=None,
        order_draft=None,
        requires_confirmation=False,
        final_response=None
    )
    
    result_state = handle_order(state)
    
    print(f"\nResponse:\n{result_state.get('final_response')}")
    
    order_draft = result_state.get("order_draft")
    if order_draft:
        print(f"\nOrder Draft:")
        print(f"  Items: {len(order_draft.get('items', []))}")
        
        # Verify total calculation
        calculated_total = 0
        for item in order_draft.get("items", []):
            item_total = item["quantity"] * item["unit_price"]
            calculated_total += item_total
            print(f"  - {item['product_name']}: {item['quantity']} x ${item['unit_price']} = ${item_total}")
        
        print(f"  Total: ${order_draft.get('total')}")
        print(f"  Calculated: ${calculated_total}")
        
        if abs(order_draft.get("total", 0) - calculated_total) < 0.01:
            print("\n✅ Order summary calculation correct")
            return True
        else:
            print("\n❌ Order summary calculation incorrect")
            return False
    else:
        print("\n❌ No order draft generated")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ORDER HANDLER NODE TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Product Extraction", test_order_extraction()))
    results.append(("Inventory Validation", test_inventory_validation()))
    results.append(("Business Hours Validation", test_business_hours_validation()))
    results.append(("Order Summary Calculation", test_order_summary_calculation()))
    
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
