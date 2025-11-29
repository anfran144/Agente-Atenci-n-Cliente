"""
LangGraph Agent Foundation for Multi-Tenant Customer Service

This module implements the conversational agent workflow using LangGraph.
It defines the agent state, workflow graph, and placeholder nodes for
intent classification and handling different conversation flows.

Requirements: 3.1, 3.3
"""

import os
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentState(TypedDict):
    """
    State maintained throughout the agent conversation workflow.
    
    This state is passed between nodes in the LangGraph workflow and
    accumulates information as the conversation progresses.
    """
    tenant_id: str  # ID of the business/tenant
    conversation_id: str  # Unique conversation identifier
    messages: List[BaseMessage]  # Conversation message history
    intent: Optional[str]  # Classified intent (faq, order_create, complaint, review, other)
    context: Optional[str]  # Retrieved context from RAG or database
    order_draft: Optional[Dict[str, Any]]  # Draft order with products and quantities
    requires_confirmation: bool  # Whether user confirmation is needed
    final_response: Optional[str]  # Final response to send to user
    user_context: Optional[Dict[str, Any]]  # User info for personalization (name, preferences, history)
    conversation_context: Optional[Dict[str, Any]]  # Conversation state tracking (has_active_order, last_intent, etc.)


# Initialize Groq LLM for intent classification
def get_llm():
    """Get configured Groq LLM instance."""
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return ChatGroq(api_key=api_key, model=model, temperature=0)


# Intent classification prompt with few-shot examples
INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a customer service chatbot. Classify the user's message into exactly ONE of these categories:

- faq: Questions about hours, location, payment methods, menu, allergens, products available, prices, or general information. ALSO includes requests to see the menu or product list when NO order is active.
- order_create: User wants to place a NEW order with SPECIFIC products mentioned (e.g., "quiero 2 pizzas", "dame un café"). ONLY use this when there is NO active order.
- order_update: User wants to modify an existing order. This includes: adding items ("y también quiero...", "agrégame..."), removing items, canceling, or asking about menu/products when an order is already active. CRITICAL: If there is an ACTIVE ORDER and user mentions ANY product, this is order_update, NOT order_create.
- complaint: User is expressing dissatisfaction, reporting a problem, or making a complaint
- review: User is leaving positive feedback, a rating, or a review
- other: Message doesn't fit any of the above categories (greetings, unclear messages)

CRITICAL RULES:
1. If the user asks about the menu or products BEFORE ordering, classify as "faq"
2. If there is an ACTIVE ORDER (see context below) and user wants to add products, classify as "order_update"
3. Words like "y", "también", "además", "and", "also" often indicate adding to an existing order

Examples:

User: "What time do you close today?"
Intent: faq

User: "What's on the menu?"
Intent: faq

User: "¿Qué tienen disponible?"
Intent: faq

User: "Quiero ver el menú"
Intent: faq

User: "¿Cuáles son los productos?"
Intent: faq

User: "¿Qué me recomiendas?"
Intent: faq

User: "Quiero pedir algo, ¿qué tienen?"
Intent: faq

User: "I'd like to order 2 pizzas and a salad"
Intent: order_create

User: "Quiero pedir un café con leche y dos croissants"
Intent: order_create

User: "Dame 3 empanadas"
Intent: order_create

User: "Can I add fries to my order?"
Intent: order_update

User: "Quiero agregar algo de tomar en mi orden"
Intent: order_update

User: "¿Qué bebidas tienen?" [Context: Active order exists]
Intent: order_update

User: "Puedo cancelar mi pedido?"
Intent: order_update

User: "ver menú" [Context: Active order exists]
Intent: order_update

User: "y quiero unos fideos" [Context: Active order exists]
Intent: order_update

User: "también dame una coca cola" [Context: Active order exists]
Intent: order_update

User: "y además quiero galletas" [Context: Active order exists]
Intent: order_update

User: "dame también un café" [Context: Active order exists]
Intent: order_update

User: "My food arrived cold and late"
Intent: complaint

User: "La comida estaba horrible"
Intent: complaint

User: "The service was excellent, 5 stars!"
Intent: review

User: "Todo estuvo delicioso, muy recomendado"
Intent: review

User: "Hello"
Intent: other

User: "¿Cuáles son sus horarios?"
Intent: faq

Now classify this message. Respond with ONLY the intent category (faq, order_create, order_update, complaint, review, or other), nothing else.

{context_info}
User: "{message}"
Intent:"""


def classify_intent(state: AgentState) -> AgentState:
    """
    Classify the intent of the user's message using LLM with conversational context awareness.
    
    This node analyzes the user's message and classifies it into one of:
    - faq: Frequently asked questions
    - order_create: Creating a new order
    - order_update: Updating an existing order
    - complaint: Customer complaint
    - review: Customer review/feedback
    - other: Unclassified or unclear intent
    
    CONTEXTUAL AWARENESS: If there's an active order (order_draft exists), the classification
    considers this context to provide more natural responses, like a real person would.
    
    Requirements 3.1, 3.2: Intent classification using LLM with few-shot prompt
    """
    try:
        # Get the last user message
        messages = state.get("messages", [])
        if not messages:
            state["intent"] = "other"
            return state
        
        # Extract the text from the last message
        last_message = messages[-1]
        if isinstance(last_message, BaseMessage):
            user_message = last_message.content
        else:
            user_message = str(last_message)
        
        # Check for active order context (like a real person would remember)
        order_draft = state.get("order_draft")
        has_active_order = order_draft is not None and len(order_draft.get("items", [])) > 0
        
        # Build context information for the classifier
        context_info = ""
        if has_active_order:
            context_info = "CONTEXT: User has an ACTIVE ORDER in progress with items already selected.\n"
        
        # Initialize LLM
        llm = get_llm()
        
        # Create the classification prompt with context
        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            message=user_message,
            context_info=context_info
        )
        
        # Get classification from LLM
        response = llm.invoke([HumanMessage(content=prompt)])
        intent = response.content.strip().lower()
        
        # Validate intent is one of the expected categories
        valid_intents = ["faq", "order_create", "order_update", "complaint", "review", "other"]
        if intent not in valid_intents:
            # If LLM returns something unexpected, default to "other"
            intent = "other"
        
        # CONTEXTUAL OVERRIDE: If we have an active order, redirect to order_update
        # This handles cases where the LLM incorrectly classifies as order_create or faq
        if has_active_order:
            user_message_lower = user_message.lower()
            
            # Override order_create to order_update when there's an active order
            # The user is adding to their existing order, not creating a new one
            if intent == "order_create":
                intent = "order_update"
                print(f"[Context Override] Changed intent from 'order_create' to 'order_update' due to active order")
            
            # Override faq to order_update when asking about menu/products during active order
            elif intent == "faq":
                menu_keywords = ["menú", "menu", "productos", "products", "qué tienen", "what do you have", 
                               "disponible", "available", "opciones", "options", "bebidas", "drinks",
                               "comidas", "food", "postres", "desserts"]
                if any(keyword in user_message_lower for keyword in menu_keywords):
                    intent = "order_update"
                    print(f"[Context Override] Changed intent from 'faq' to 'order_update' due to active order")
        
        # Store the classified intent in state
        state["intent"] = intent
        
        # Update conversation context
        conversation_context = state.get("conversation_context", {})
        conversation_context["last_intent"] = intent
        conversation_context["has_active_order"] = has_active_order
        state["conversation_context"] = conversation_context
        
    except Exception as e:
        # If classification fails, default to "other"
        print(f"Intent classification error: {e}")
        state["intent"] = "other"
    
    return state


def handle_faq(state: AgentState) -> AgentState:
    """
    Handle FAQ queries using RAG (Retrieval-Augmented Generation) with ENRICHED CONTEXT.
    
    This node retrieves relevant context from the knowledge base,
    enriches it with business insights, popular products, and user history,
    then generates an intelligent response that can recommend based on real data.
    
    Requirements 1.1, 1.2, 1.3: FAQ handling with RAG and tenant filtering
    """
    from database import get_supabase_client
    from rag_service import RAGService
    from repository import Repository
    
    try:
        # Get the user's message
        messages = state.get("messages", [])
        if not messages:
            state["final_response"] = "I'm here to help! What would you like to know?"
            return state
        
        last_message = messages[-1]
        if isinstance(last_message, BaseMessage):
            user_query = last_message.content
        else:
            user_query = str(last_message)
        
        # Get tenant_id from state
        tenant_id = state.get("tenant_id")
        if not tenant_id:
            state["final_response"] = "I'm sorry, I couldn't identify your business. Please try again."
            return state
        
        # Get user context for personalization
        user_context = state.get("user_context")
        user_id = user_context.get("user_id") if user_context else None
        
        # Initialize services
        supabase_client = get_supabase_client()
        rag_service = RAGService(supabase_client)
        repo = Repository(supabase_client)
        
        # Retrieve relevant context using RAG (Requirement 1.2, 1.3)
        rag_context = rag_service.retrieve_context(user_query, tenant_id, top_k=5)
        
        # Store context in state
        state["context"] = rag_context
        
        # ============================================
        # ENRICHED CONTEXT - Business Intelligence
        # ============================================
        enriched = repo.get_enriched_context(tenant_id, user_id)
        
        # Build enriched context string for LLM
        enriched_context = ""
        
        # Top products this week (for recommendations)
        if enriched.get("top_products_week"):
            top_prods = enriched["top_products_week"][:3]
            enriched_context += "\n\nPRODUCTOS MÁS PEDIDOS ESTA SEMANA:\n"
            for p in top_prods:
                enriched_context += f"- {p['name']}: {p.get('order_count', 0)} pedidos (${p['price']})\n"
        
        # Popular products by mentions
        if enriched.get("popular_products"):
            pop_prods = enriched["popular_products"][:3]
            enriched_context += "\nPRODUCTOS MÁS CONSULTADOS:\n"
            for p in pop_prods:
                enriched_context += f"- {p['name']}: {p.get('mention_count', 0)} menciones\n"
        
        # Tenant insights
        insights = enriched.get("tenant_insights", {})
        if insights:
            enriched_context += f"\nINFORMACIÓN DEL NEGOCIO:\n"
            if insights.get("total_orders"):
                enriched_context += f"- Total de pedidos históricos: {insights['total_orders']}\n"
            if insights.get("avg_rating"):
                enriched_context += f"- Calificación promedio: {insights['avg_rating']}/5\n"
            if insights.get("peak_hours"):
                hours = [f"{h['hour']}:00" for h in insights["peak_hours"][:2]]
                enriched_context += f"- Horas pico: {', '.join(hours)}\n"
        
        # User history (if available)
        if enriched.get("user_order_history"):
            user_orders = enriched["user_order_history"][:3]
            enriched_context += f"\nHISTORIAL DEL CLIENTE:\n"
            for order in user_orders:
                items = order.get("order_items", [])
                if items:
                    item_names = [f"{i.get('quantity', 1)}x producto" for i in items[:2]]
                    enriched_context += f"- Pedido anterior: {', '.join(item_names)} (${order.get('total_amount', 0)})\n"
        
        # User preferences
        if enriched.get("user_preferences"):
            prefs = enriched["user_preferences"][:3]
            enriched_context += f"\nPREFERENCIAS CONOCIDAS DEL CLIENTE:\n"
            for p in prefs:
                enriched_context += f"- {p['preference_type']}: {p['preference_value']} (confianza: {p['confidence']:.0%})\n"
        
        # Network patterns
        if enriched.get("network_patterns"):
            patterns = enriched["network_patterns"][:2]
            enriched_context += f"\nPATRONES DE LA RED (insights globales):\n"
            for p in patterns:
                if p.get("pattern"):
                    enriched_context += f"- {p['pattern']}\n"
        
        # Build personalization context
        personalization = ""
        if user_context:
            user_name = user_context.get("user_name", "")
            is_returning = user_context.get("is_returning_customer", False)
            
            if user_name:
                personalization += f"\nNombre del cliente: {user_name}"
            if is_returning:
                personalization += f"\nEs un cliente recurrente - sé cálido y reconoce su lealtad."
        
        # Generate response using LLM with FULL enriched context
        llm = get_llm()
        
        response_prompt = f"""Eres un asistente de atención al cliente amigable e inteligente. 

CAPACIDADES ESPECIALES:
- Puedes RECOMENDAR productos basándote en los datos reales de ventas y popularidad
- Puedes PERSONALIZAR respuestas según el historial del cliente
- Puedes usar INSIGHTS del negocio para dar mejores respuestas

REGLAS:
1. Responde en el MISMO IDIOMA que el usuario (español si escribe en español)
2. Si el usuario pide una recomendación, USA los datos de productos más pedidos
3. Si conoces preferencias del cliente, menciónalas naturalmente
4. Sé conciso pero informativo

{f"Dirígete al cliente por su nombre: {user_context.get('user_name')}" if user_context and user_context.get('user_name') else ""}

CONTEXTO DE FAQs Y PRODUCTOS:
{rag_context}

INTELIGENCIA DE NEGOCIO (usa esto para recomendar):
{enriched_context}
{personalization}

PREGUNTA DEL USUARIO: {user_query}

Responde de forma útil, amigable y personalizada. Si pide recomendación, recomienda basándote en los datos reales:"""
        
        response = llm.invoke([HumanMessage(content=response_prompt)])
        state["final_response"] = response.content
        
    except Exception as e:
        print(f"FAQ handler error: {e}")
        import traceback
        traceback.print_exc()
        state["final_response"] = (
            "I apologize, but I encountered an issue processing your question. "
            "Please try again or contact us directly for assistance."
        )
    
    return state


def handle_order(state: AgentState) -> AgentState:
    """
    Handle order creation and updates with user personalization.
    
    This node extracts products and quantities, validates inventory,
    checks business hours, generates order summaries, and persists confirmed orders.
    Uses user context to personalize responses and suggest previous orders.
    
    Requirement 2.1, 2.2, 2.3, 2.4, 2.5, 2.6: Order processing and persistence
    """
    from database import get_supabase_client
    from repository import Repository
    import json
    from datetime import datetime
    import pytz
    
    try:
        # Get user context for personalization
        user_context = state.get("user_context")
        user_name = user_context.get("user_name", "") if user_context else ""
        is_returning = user_context.get("is_returning_customer", False) if user_context else False
        recent_orders = user_context.get("recent_orders", []) if user_context else []
        
        # Get the user's message
        messages = state.get("messages", [])
        if not messages:
            # Personalized greeting for order intent
            if user_name and is_returning and recent_orders:
                last_order = recent_orders[0] if recent_orders else None
                greeting = f"¡Hola {user_name}! Me alegra verte de nuevo. "
                if last_order:
                    greeting += "¿Te gustaría repetir tu último pedido o prefieres algo diferente?"
                state["final_response"] = greeting
            elif user_name:
                state["final_response"] = f"¡Hola {user_name}! ¿Qué te gustaría pedir hoy?"
            else:
                state["final_response"] = "I'm here to help with your order! What would you like to order?"
            state["requires_confirmation"] = False
            return state
        
        last_message = messages[-1]
        if isinstance(last_message, BaseMessage):
            user_message = last_message.content
        else:
            user_message = str(last_message)
        
        # Check if this is a confirmation message for an existing order draft
        # Requirement 2.5: Handle order confirmation
        order_draft = state.get("order_draft")
        if order_draft:
            # Check if user is confirming the order
            confirmation_keywords = ["sí", "si", "yes", "confirmar", "confirm", "ok", "okay", "dale", "perfecto", "perfect"]
            rejection_keywords = ["no", "cancelar", "cancel", "cambiar", "change", "modificar", "modify"]
            
            user_message_lower = user_message.lower().strip()
            
            # Check for confirmation
            is_confirmation = any(keyword in user_message_lower for keyword in confirmation_keywords)
            is_rejection = any(keyword in user_message_lower for keyword in rejection_keywords)
            
            if is_confirmation and not is_rejection:
                # User confirmed the order - persist it (Requirement 2.5)
                tenant_id = state.get("tenant_id")
                conversation_id = state.get("conversation_id")
                
                if not tenant_id or not conversation_id:
                    state["final_response"] = "I'm sorry, there was an error processing your order. Please try again."
                    state["requires_confirmation"] = False
                    state["order_draft"] = None
                    return state
                
                # Initialize repository
                supabase_client = get_supabase_client()
                repo = Repository(supabase_client)
                
                # Create order record (Requirement 2.5)
                order = repo.create_order(
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    total_amount=order_draft["total"],
                    status="pending"
                )
                
                # Create order items (Requirement 2.5)
                order_items = repo.create_order_items(
                    order_id=order["id"],
                    items=order_draft["items"]
                )
                
                # Generate personalized confirmation response
                if user_name:
                    state["final_response"] = (
                        f"✅ ¡Pedido confirmado, {user_name}! ID: {order['id']}\n\n"
                        f"Total: ${order_draft['total']:,.0f}\n\n"
                        f"Ya estamos preparando tu pedido. ¡Gracias por tu compra! 🎉"
                    )
                else:
                    state["final_response"] = (
                        f"✅ Your order has been confirmed! Order ID: {order['id']}\n\n"
                        f"Total: ${order_draft['total']:,.0f}\n\n"
                        f"We'll start preparing your order right away. Thank you for your purchase!"
                    )
                state["requires_confirmation"] = False
                state["order_draft"] = None
                
                return state
            
            elif is_rejection:
                # User rejected or wants to modify the order
                if user_name:
                    state["final_response"] = (
                        f"¡Sin problema, {user_name}! Tu pedido ha sido cancelado. "
                        "Dime qué te gustaría pedir en su lugar."
                    )
                else:
                    state["final_response"] = (
                        "No problem! Your order has been cancelled. "
                        "Feel free to tell me what you'd like to order instead."
                    )
                state["requires_confirmation"] = False
                state["order_draft"] = None
                
                return state
            
            # If message is unclear, ask for clarification
            # Continue to process as a new order request below
        
        # If we reach here, either:
        # 1. There's no existing order draft, OR
        # 2. User's message wasn't a clear confirmation/rejection
        # Process as a new order request
        
        # Get tenant_id from state
        tenant_id = state.get("tenant_id")
        if not tenant_id:
            state["final_response"] = "I'm sorry, I couldn't identify your business. Please try again."
            state["requires_confirmation"] = False
            return state
        
        # Initialize repository
        supabase_client = get_supabase_client()
        repo = Repository(supabase_client)
        
        # Get tenant information for business hours validation (Requirement 2.3)
        tenant = repo.get_tenant(tenant_id)
        if not tenant:
            state["final_response"] = "I'm sorry, I couldn't find the business information. Please try again."
            state["requires_confirmation"] = False
            return state
        
        # Validate business hours (Requirement 2.3)
        business_hours = tenant.get("config", {}).get("business_hours", {})
        timezone_str = tenant.get("timezone", "UTC")
        
        # Get current time in tenant's timezone
        tz = pytz.timezone(timezone_str)
        current_time = datetime.now(tz)
        day_name = current_time.strftime("%A").lower()
        current_hour_minute = current_time.strftime("%H:%M")
        
        # Check if business is open
        hours_today = business_hours.get(day_name, "closed")
        is_open = False
        
        if hours_today != "closed":
            # Parse business hours (can be "HH:MM-HH:MM" or "HH:MM-HH:MM,HH:MM-HH:MM" for split shifts)
            time_ranges = hours_today.split(",")
            for time_range in time_ranges:
                if "-" in time_range:
                    start_time, end_time = time_range.strip().split("-")
                    
                    # Handle midnight crossing (e.g., "12:00-00:00" means noon to midnight)
                    if end_time == "00:00":
                        # If end time is 00:00, it means midnight (end of day)
                        # Check if current time is between start and 23:59
                        if start_time <= current_hour_minute <= "23:59":
                            is_open = True
                            break
                    else:
                        # Normal time range
                        if start_time <= current_hour_minute <= end_time:
                            is_open = True
                            break
        
        if not is_open:
            state["final_response"] = (
                f"I'm sorry, but we're currently closed. "
                f"Our hours today ({day_name.capitalize()}) are: {hours_today}. "
                f"Please come back during our business hours!"
            )
            state["requires_confirmation"] = False
            return state
        
        # Get all products for this tenant (Requirement 2.1)
        products = repo.get_products(tenant_id)
        if not products:
            state["final_response"] = "I'm sorry, but I couldn't find any products available. Please try again later."
            state["requires_confirmation"] = False
            return state
        
        # Create a product catalog for the LLM
        product_catalog = []
        for p in products:
            product_catalog.append({
                "id": p["id"],
                "name": p["name"],
                "description": p.get("description", ""),
                "category": p.get("category", ""),
                "price": float(p["price"])
            })
        
        # Extract products and quantities using LLM with structured output (Requirement 2.1)
        llm = get_llm()
        
        extraction_prompt = f"""You are an order extraction assistant. Extract the products and quantities from the user's message.

Available products:
{json.dumps(product_catalog, indent=2, ensure_ascii=False)}

User message: "{user_message}"

Extract the products mentioned and their quantities. Return a JSON object with this exact structure:
{{
  "items": [
    {{"product_id": "uuid-here", "product_name": "Product Name", "quantity": 2}},
    ...
  ]
}}

If you cannot identify any products from the catalog, return {{"items": []}}.
Only include products that are clearly mentioned in the user's message and exist in the catalog.
Match products by name, considering variations and synonyms.

Return ONLY the JSON object, nothing else."""
        
        response = llm.invoke([HumanMessage(content=extraction_prompt)])
        
        try:
            # Parse the LLM response
            extracted_data = json.loads(response.content.strip())
            items = extracted_data.get("items", [])
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            try:
                extracted_data = json.loads(content)
                items = extracted_data.get("items", [])
            except:
                items = []
        
        if not items:
            # No specific products found - offer to show menu
            if user_name:
                state["final_response"] = (
                    f"¡Claro {user_name}! Para hacer tu pedido necesito saber qué productos te gustaría. "
                    "¿Quieres que te muestre nuestro menú? Solo dime 'ver menú' o pregúntame qué tenemos disponible."
                )
            else:
                state["final_response"] = (
                    "I'm sorry, I couldn't identify any products from your message. "
                    "Could you please specify which products you'd like to order? "
                    "You can ask me about our menu if you'd like to see what's available."
                )
            state["requires_confirmation"] = False
            return state
        
        # Validate inventory and build order summary (Requirement 2.2, 2.4)
        order_items = []
        insufficient_stock_items = []
        total_amount = 0.0
        
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
            product_name = item.get("product_name", "Unknown")
            
            # Get inventory for this product (Requirement 2.2)
            inventory = repo.get_inventory_item(tenant_id, product_id)
            
            if not inventory:
                insufficient_stock_items.append({
                    "name": product_name,
                    "requested": quantity,
                    "available": 0
                })
                continue
            
            available_stock = inventory.get("stock_quantity", 0)
            
            # Check if sufficient stock (Requirement 2.6)
            if available_stock < quantity:
                insufficient_stock_items.append({
                    "name": product_name,
                    "requested": quantity,
                    "available": available_stock
                })
                continue
            
            # Find product details for price
            product_details = next((p for p in products if p["id"] == product_id), None)
            if not product_details:
                continue
            
            unit_price = float(product_details["price"])
            item_total = unit_price * quantity
            total_amount += item_total
            
            order_items.append({
                "product_id": product_id,
                "product_name": product_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "item_total": item_total
            })
        
        # Handle insufficient stock scenario (Requirement 2.6)
        if insufficient_stock_items and not order_items:
            # All items have insufficient stock
            stock_messages = []
            for item in insufficient_stock_items:
                if item["available"] > 0:
                    stock_messages.append(
                        f"- {item['name']}: You requested {item['requested']}, but we only have {item['available']} available"
                    )
                else:
                    stock_messages.append(
                        f"- {item['name']}: Currently out of stock"
                    )
            
            state["final_response"] = (
                "I'm sorry, but we don't have sufficient stock for your order:\n\n" +
                "\n".join(stock_messages) +
                "\n\nWould you like to adjust your order?"
            )
            state["requires_confirmation"] = False
            return state
        
        if insufficient_stock_items:
            # Some items have insufficient stock
            stock_messages = []
            for item in insufficient_stock_items:
                if item["available"] > 0:
                    stock_messages.append(
                        f"- {item['name']}: You requested {item['requested']}, but we only have {item['available']} available"
                    )
                else:
                    stock_messages.append(
                        f"- {item['name']}: Currently out of stock"
                    )
            
            stock_warning = "\n\n⚠️ Note: Some items have insufficient stock:\n" + "\n".join(stock_messages)
        else:
            stock_warning = ""
        
        if not order_items:
            state["final_response"] = "I couldn't process any items from your order. Please try again."
            state["requires_confirmation"] = False
            return state
        
        # Generate order summary with personalization (Requirement 2.4)
        if user_name:
            summary_lines = [f"¡Perfecto {user_name}! Aquí está el resumen de tu pedido:\n"]
        else:
            summary_lines = ["Here's your order summary:\n"]
        
        for item in order_items:
            summary_lines.append(
                f"• {item['product_name']} x{item['quantity']} - ${item['unit_price']:,.0f} c/u = ${item['item_total']:,.0f}"
            )
        
        summary_lines.append(f"\n**Total: ${total_amount:,.0f}**")
        
        if stock_warning:
            summary_lines.append(stock_warning)
        
        if user_name:
            summary_lines.append(f"\n\n¿Confirmamos tu pedido, {user_name}?")
        else:
            summary_lines.append("\n\nWould you like to confirm this order?")
        
        # Store order draft in state
        state["order_draft"] = {
            "items": order_items,
            "total": total_amount
        }
        
        # Set requires_confirmation flag (Requirement 2.4)
        state["requires_confirmation"] = True
        state["final_response"] = "\n".join(summary_lines)
        
    except Exception as e:
        print(f"Order handler error: {e}")
        import traceback
        traceback.print_exc()
        state["final_response"] = (
            "I apologize, but I encountered an issue processing your order. "
            "Please try again or contact us directly for assistance."
        )
        state["requires_confirmation"] = False
    
    return state


def handle_order_update(state: AgentState) -> AgentState:
    """
    Handle updates to existing orders with natural, contextual responses.
    
    This function makes the agent behave like a real person by:
    - Remembering there's an active order
    - Understanding when the user wants to add items
    - Showing relevant products based on context (e.g., drinks, desserts)
    - Maintaining the existing order while adding new items
    
    Handles:
    - Adding items to active order ("quiero agregar algo de tomar")
    - Showing menu during an active order ("ver menú", "qué bebidas tienen")
    - Removing items from order
    - Canceling order
    """
    from database import get_supabase_client
    from repository import Repository
    import json
    
    try:
        # Get user context for personalization
        user_context = state.get("user_context")
        user_name = user_context.get("user_name", "") if user_context else ""
        
        # Get the user's message
        messages = state.get("messages", [])
        if not messages:
            state["final_response"] = "I'm here to help with your order! What would you like to do?"
            state["requires_confirmation"] = False
            return state
        
        last_message = messages[-1]
        if isinstance(last_message, BaseMessage):
            user_message = last_message.content
        else:
            user_message = str(last_message)
        
        # Get order_draft from state
        order_draft = state.get("order_draft")
        
        # If there's no active order, redirect to order creation
        if not order_draft or len(order_draft.get("items", [])) == 0:
            if user_name:
                state["final_response"] = (
                    f"¡Hola {user_name}! Veo que aún no has iniciado un pedido. "
                    "¿Qué te gustaría ordenar?"
                )
            else:
                state["final_response"] = (
                    "I don't see an active order. "
                    "What would you like to order?"
                )
            state["requires_confirmation"] = False
            return state
        
        # Get tenant_id
        tenant_id = state.get("tenant_id")
        if not tenant_id:
            state["final_response"] = "I'm sorry, I couldn't identify your business. Please try again."
            state["requires_confirmation"] = False
            return state
        
        # Initialize repository
        supabase_client = get_supabase_client()
        repo = Repository(supabase_client)
        
        # Get all products for this tenant
        products = repo.get_products(tenant_id)
        if not products:
            state["final_response"] = "I'm sorry, but I couldn't find any products available. Please try again later."
            state["requires_confirmation"] = False
            return state
        
        # Determine what the user wants to do
        user_message_lower = user_message.lower()
        
        # Check for cancellation keywords
        cancel_keywords = ["cancelar", "cancel", "eliminar pedido", "delete order", "borrar", "no quiero"]
        if any(keyword in user_message_lower for keyword in cancel_keywords):
            # User wants to cancel the order
            if user_name:
                state["final_response"] = (
                    f"Entendido, {user_name}. He cancelado tu pedido. "
                    "Si cambias de opinión, con gusto puedo ayudarte a crear uno nuevo."
                )
            else:
                state["final_response"] = (
                    "I've canceled your order. "
                    "If you change your mind, I'd be happy to help you create a new one."
                )
            state["order_draft"] = None
            state["requires_confirmation"] = False
            return state
        
        # Detect what category the user is interested in
        category_keywords = {
            "bebidas": ["bebida", "drink", "tomar", "café", "coffee", "jugo", "juice", "té", "tea"],
            "postres": ["postre", "dessert", "dulce", "sweet", "pastel", "cake"],
            "comidas": ["comida", "food", "comer", "almuerzo", "lunch", "cena", "dinner"]
        }
        
        detected_category = None
        for category, keywords in category_keywords.items():
            if any(keyword in user_message_lower for keyword in keywords):
                detected_category = category
                break
        
        # Check if user is mentioning specific products or just asking to see options
        add_keywords = ["agregar", "add", "añadir", "quiero", "want", "also", "también"]
        menu_keywords = ["menú", "menu", "productos", "products", "opciones", "options", 
                        "qué tienen", "what do you have", "disponible", "available", "ver"]
        
        is_asking_menu = any(keyword in user_message_lower for keyword in menu_keywords)
        is_adding = any(keyword in user_message_lower for keyword in add_keywords)
        
        # Try to extract specific products from the message
        llm = get_llm()
        
        # Create a product catalog
        product_catalog = []
        for p in products:
            product_catalog.append({
                "id": p["id"],
                "name": p["name"],
                "description": p.get("description", ""),
                "category": p.get("category", ""),
                "price": float(p["price"])
            })
        
        extraction_prompt = f"""You are an order extraction assistant. Extract the products and quantities from the user's message.

Available products:
{json.dumps(product_catalog, indent=2, ensure_ascii=False)}

User message: "{user_message}"

Extract the products mentioned and their quantities. Return a JSON object with this exact structure:
{{
  "items": [
    {{"product_id": "uuid-here", "product_name": "Product Name", "quantity": 2}},
    ...
  ]
}}

If you cannot identify any SPECIFIC products from the catalog, return {{"items": []}}.
Only include products that are clearly mentioned in the user's message and exist in the catalog.
Match products by name, considering variations and synonyms.

Return ONLY the JSON object, nothing else."""
        
        response = llm.invoke([HumanMessage(content=extraction_prompt)])
        
        try:
            # Parse the LLM response
            extracted_data = json.loads(response.content.strip())
            new_items = extracted_data.get("items", [])
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            try:
                extracted_data = json.loads(content)
                new_items = extracted_data.get("items", [])
            except:
                new_items = []
        
        # If no specific products found, show relevant menu
        if not new_items:
            # Filter products by detected category if any
            if detected_category:
                filtered_products = [p for p in products if detected_category.lower() in p.get("category", "").lower()]
            else:
                filtered_products = products
            
            # Build menu display
            if detected_category == "bebidas":
                category_name = "bebidas" if "bebida" in user_message_lower else "drinks"
            elif detected_category:
                category_name = detected_category
            else:
                category_name = "productos" if any(c in user_message_lower for c in "áéíóú") else "products"
            
            menu_lines = []
            if user_name:
                menu_lines.append(f"¡Claro {user_name}! Aquí están nuestras opciones de {category_name}:\n")
            else:
                menu_lines.append(f"Here are our {category_name}:\n")
            
            for p in filtered_products[:10]:  # Limit to 10 items
                menu_lines.append(f"• {p['name']} - ${float(p['price']):,.0f}")
            
            if user_name:
                menu_lines.append(f"\n¿Cuál te gustaría agregar a tu pedido, {user_name}?")
            else:
                menu_lines.append("\nWhich one would you like to add to your order?")
            
            state["final_response"] = "\n".join(menu_lines)
            state["requires_confirmation"] = False
            return state
        
        # Add new items to existing order
        existing_items = order_draft.get("items", [])
        total_amount = order_draft.get("total", 0.0)
        
        added_items = []
        insufficient_stock_items = []
        
        for item in new_items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
            product_name = item.get("product_name", "Unknown")
            
            # Get inventory
            inventory = repo.get_inventory_item(tenant_id, product_id)
            
            if not inventory:
                insufficient_stock_items.append({
                    "name": product_name,
                    "requested": quantity,
                    "available": 0
                })
                continue
            
            available_stock = inventory.get("stock_quantity", 0)
            
            if available_stock < quantity:
                insufficient_stock_items.append({
                    "name": product_name,
                    "requested": quantity,
                    "available": available_stock
                })
                continue
            
            # Find product details
            product_details = next((p for p in products if p["id"] == product_id), None)
            if not product_details:
                continue
            
            unit_price = float(product_details["price"])
            item_total = unit_price * quantity
            total_amount += item_total
            
            new_order_item = {
                "product_id": product_id,
                "product_name": product_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "item_total": item_total
            }
            
            existing_items.append(new_order_item)
            added_items.append(new_order_item)
        
        if not added_items and insufficient_stock_items:
            # No items could be added due to stock
            stock_messages = []
            for item in insufficient_stock_items:
                if item["available"] > 0:
                    stock_messages.append(
                        f"- {item['name']}: Solicitaste {item['requested']}, pero solo tenemos {item['available']} disponibles"
                    )
                else:
                    stock_messages.append(f"- {item['name']}: Agotado")
            
            state["final_response"] = (
                "Lo siento, no pude agregar estos items por falta de stock:\n\n" +
                "\n".join(stock_messages) +
                "\n\n¿Te gustaría ordenar otra cosa?"
            )
            state["requires_confirmation"] = False
            return state
        
        # Successfully added items - show updated order summary
        if user_name:
            summary_lines = [f"¡Perfecto {user_name}! He agregado a tu pedido:\n"]
        else:
            summary_lines = ["Great! I've added to your order:\n"]
        
        for item in added_items:
            summary_lines.append(
                f"• {item['product_name']} x{item['quantity']} - ${item['unit_price']:,.0f} c/u = ${item['item_total']:,.0f}"
            )
        
        summary_lines.append(f"\n**Resumen completo de tu pedido:**\n")
        
        for item in existing_items:
            summary_lines.append(
                f"• {item['product_name']} x{item['quantity']} - ${item['unit_price']:,.0f} c/u = ${item['item_total']:,.0f}"
            )
        
        summary_lines.append(f"\n**Total: ${total_amount:,.0f}**")
        
        if user_name:
            summary_lines.append(f"\n¿Deseas agregar algo más o confirmamos tu pedido, {user_name}?")
        else:
            summary_lines.append("\nWould you like to add anything else or confirm your order?")
        
        # Update order draft
        state["order_draft"] = {
            "items": existing_items,
            "total": total_amount
        }
        
        state["requires_confirmation"] = True
        state["final_response"] = "\n".join(summary_lines)
        
    except Exception as e:
        print(f"Order update handler error: {e}")
        import traceback
        traceback.print_exc()
        state["final_response"] = (
            "I apologize, but I encountered an issue updating your order. "
            "Please try again or contact us directly for assistance."
        )
        state["requires_confirmation"] = False
    
    return state


def handle_review(state: AgentState) -> AgentState:
    """
    Handle customer reviews and complaints.
    
    This node performs sentiment analysis, extracts ratings,
    and persists feedback to the database.
    
    Requirement 7.1, 7.2, 7.3, 7.4: Review and complaint handling
    """
    from database import get_supabase_client
    from repository import Repository
    import json
    
    try:
        # Get the user's message
        messages = state.get("messages", [])
        if not messages:
            state["final_response"] = "Thank you for your feedback! How can I help you?"
            return state
        
        last_message = messages[-1]
        if isinstance(last_message, BaseMessage):
            user_message = last_message.content
        else:
            user_message = str(last_message)
        
        # Get tenant_id and conversation_id from state
        tenant_id = state.get("tenant_id")
        conversation_id = state.get("conversation_id")
        intent = state.get("intent", "review")
        
        if not tenant_id or not conversation_id:
            state["final_response"] = "I'm sorry, I couldn't process your feedback. Please try again."
            return state
        
        # Initialize LLM for sentiment analysis and rating extraction
        llm = get_llm()
        
        # Perform sentiment analysis and rating extraction (Requirement 7.2, 7.4)
        analysis_prompt = f"""You are a sentiment analysis assistant. Analyze the user's message and extract:
1. Whether this is a complaint (negative sentiment) or a positive review
2. A rating from 1-5 (1 = very negative, 5 = very positive)
3. The main sentiment/emotion

User message: "{user_message}"

Return a JSON object with this exact structure:
{{
  "is_complaint": true or false,
  "rating": 1-5,
  "sentiment": "description of sentiment"
}}

Guidelines:
- If the message expresses dissatisfaction, problems, or complaints, set is_complaint to true and rating 1-2
- If the message is neutral or unclear, set rating to 3
- If the message expresses satisfaction or praise, set is_complaint to false and rating 4-5
- Consider words like: malo/bad, horrible/terrible, excelente/excellent, delicioso/delicious, etc.

Return ONLY the JSON object, nothing else."""
        
        response = llm.invoke([HumanMessage(content=analysis_prompt)])
        
        try:
            # Parse the LLM response
            analysis_data = json.loads(response.content.strip())
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            try:
                analysis_data = json.loads(content)
            except:
                # Default to neutral if parsing fails
                analysis_data = {
                    "is_complaint": False,
                    "rating": 3,
                    "sentiment": "neutral"
                }
        
        is_complaint = analysis_data.get("is_complaint", False)
        rating = analysis_data.get("rating", 3)
        sentiment = analysis_data.get("sentiment", "neutral")
        
        # Ensure rating is within valid range
        rating = max(1, min(5, rating))
        
        # Initialize repository
        supabase_client = get_supabase_client()
        repo = Repository(supabase_client)
        
        # Persist review/complaint to database
        # Requirement 7.1: Complaints with negative rating
        # Requirement 7.2: Positive reviews with extracted rating
        # Requirement 7.3: Mark complaints with requires_attention flag
        # Requirement 7.4: Extract rating, comment, and source
        requires_attention = is_complaint or rating <= 2
        
        review = repo.create_review(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            rating=rating,
            comment=user_message,
            source="chat",
            requires_attention=requires_attention
        )
        
        # Get user context for personalization
        user_context = state.get("user_context")
        user_name = user_context.get("user_name", "") if user_context else ""
        
        # Generate empathetic response based on sentiment with personalization
        if is_complaint or rating <= 2:
            # Empathetic response for complaints (Requirement 7.1, 7.3)
            if user_name:
                state["final_response"] = (
                    f"Lamento mucho escuchar esto, {user_name}. Tu opinión es muy importante para nosotros "
                    "y he registrado tu queja para que nuestro equipo la atienda de inmediato. "
                    "Nos tomamos estos asuntos muy en serio y trabajaremos para resolver tus inquietudes. "
                    "¿Hay algo más en lo que pueda ayudarte?"
                )
            else:
                state["final_response"] = (
                    "I'm truly sorry to hear about your experience. Your feedback is very important to us, "
                    "and I've recorded your complaint for immediate attention from our team. "
                    "We take these matters seriously and will work to address your concerns. "
                    "Is there anything else I can help you with right now?"
                )
        elif rating >= 4:
            # Grateful response for positive reviews (Requirement 7.2)
            if user_name:
                state["final_response"] = (
                    f"¡Muchísimas gracias por tus palabras, {user_name}! 🌟 Nos alegra mucho saber que tuviste "
                    "una excelente experiencia. Tu opinión significa mucho para nosotros y motiva a nuestro equipo "
                    "a seguir dando lo mejor. ¡Esperamos verte pronto de nuevo!"
                )
            else:
                state["final_response"] = (
                    "Thank you so much for your kind words! We're thrilled to hear you had a great experience. "
                    "Your feedback means a lot to us and motivates our team to keep delivering excellent service. "
                    "We look forward to serving you again soon!"
                )
        else:
            # Neutral response for moderate feedback
            if user_name:
                state["final_response"] = (
                    f"Gracias por compartir tu opinión, {user_name}. Apreciamos que te hayas tomado el tiempo "
                    "de contarnos sobre tu experiencia. Si hay algo específico que podamos mejorar o en lo que "
                    "podamos ayudarte, no dudes en decírnoslo."
                )
            else:
                state["final_response"] = (
                    "Thank you for sharing your feedback with us. We appreciate you taking the time to let us know "
                    "about your experience. If there's anything specific we can improve or help you with, "
                    "please don't hesitate to let us know!"
                )
        
    except Exception as e:
        print(f"Review handler error: {e}")
        import traceback
        traceback.print_exc()
        state["final_response"] = (
            "Thank you for your feedback. I apologize, but I encountered an issue recording it. "
            "Please feel free to share your thoughts again, and we'll make sure they're heard."
        )
    
    return state


def generate_response(state: AgentState) -> AgentState:
    """
    Generate the final response to the user.
    
    This node formats the response based on intent type and
    applies tenant-specific tone from configuration.
    
    Requirement 1.4, 3.4: Response generation
    """
    from database import get_supabase_client
    from repository import Repository
    
    try:
        # If a final_response was already set by a handler node, use it
        if state.get("final_response"):
            # Apply tenant-specific tone if available
            final_response = state["final_response"]
            
            # Get tenant configuration for tone customization
            tenant_id = state.get("tenant_id")
            if tenant_id:
                try:
                    supabase_client = get_supabase_client()
                    repo = Repository(supabase_client)
                    tenant = repo.get_tenant(tenant_id)
                    
                    if tenant:
                        # Check if tenant has a custom tone configuration
                        config = tenant.get("config", {})
                        tone = config.get("tone", "friendly")
                        
                        # Apply tone adjustments if needed
                        # For now, we keep the response as-is since handlers already
                        # generate appropriate responses. This is a hook for future
                        # tone customization if needed.
                        state["final_response"] = final_response
                except Exception as e:
                    # If we can't get tenant config, just use the response as-is
                    print(f"Could not apply tenant tone: {e}")
                    state["final_response"] = final_response
            
            return state
        
        # If no final_response was set, generate one based on intent
        intent = state.get("intent", "other")
        
        # Get user context for personalization
        user_context = state.get("user_context")
        user_name = user_context.get("user_name", "") if user_context else ""
        is_returning = user_context.get("is_returning_customer", False) if user_context else False
        
        # Handle "other" intent with helpful fallback message (Requirement 3.4)
        if intent == "other":
            if user_name and is_returning:
                state["final_response"] = (
                    f"¡Hola de nuevo, {user_name}! 👋 Me alegra verte. Puedo ayudarte con:\n"
                    "• Preguntas sobre horarios, ubicación, menú y métodos de pago\n"
                    "• Realizar pedidos de nuestros productos\n"
                    "• Recibir tus comentarios y reseñas\n\n"
                    "¿En qué puedo ayudarte hoy?"
                )
            elif user_name:
                state["final_response"] = (
                    f"¡Hola {user_name}! 👋 Bienvenido/a. Puedo ayudarte con:\n"
                    "• Preguntas sobre horarios, ubicación, menú y métodos de pago\n"
                    "• Realizar pedidos de nuestros productos\n"
                    "• Recibir tus comentarios y reseñas\n\n"
                    "¿En qué puedo ayudarte hoy?"
                )
            else:
                state["final_response"] = (
                    "I'm here to help! I can assist you with:\n"
                    "• Questions about our hours, location, menu, and payment methods\n"
                    "• Placing orders for our products\n"
                    "• Handling feedback and reviews\n\n"
                    "How can I assist you today?"
                )
        elif intent == "faq":
            # Fallback for FAQ if handler didn't set a response
            if user_name:
                state["final_response"] = (
                    f"¡Estoy aquí para responder tus preguntas, {user_name}! "
                    "Pregúntame sobre horarios, ubicación, menú o lo que necesites."
                )
            else:
                state["final_response"] = (
                    "I'm here to answer your questions! "
                    "Feel free to ask about our hours, location, menu, or anything else."
                )
        elif intent in ["order_create", "order_update"]:
            # Fallback for order intents if handler didn't set a response
            if user_name:
                state["final_response"] = (
                    f"¡Con gusto te ayudo con tu pedido, {user_name}! "
                    "Dime qué te gustaría ordenar."
                )
            else:
                state["final_response"] = (
                    "I'd be happy to help you with your order! "
                    "Please tell me what you'd like to order."
                )
        elif intent in ["complaint", "review"]:
            # Fallback for review/complaint intents if handler didn't set a response
            if user_name:
                state["final_response"] = (
                    f"Gracias por compartir tu opinión, {user_name}. "
                    "Tu retroalimentación es valiosa y nos ayuda a mejorar."
                )
            else:
                state["final_response"] = (
                    "Thank you for sharing your feedback with us. "
                    "Your input is valuable and helps us improve our service."
                )
        else:
            # Generic fallback
            if user_name:
                state["final_response"] = f"¡Hola {user_name}! ¿En qué puedo ayudarte hoy?"
            else:
                state["final_response"] = "I'm here to help! How can I assist you today?"
        
    except Exception as e:
        print(f"Response generation error: {e}")
        # Ensure we always have a response
        state["final_response"] = "I'm here to help! How can I assist you today?"
    
    return state


def route_by_intent(state: AgentState) -> str:
    """
    Conditional edge function to route based on classified intent.
    
    Routes the conversation to the appropriate handler node based
    on the intent classification.
    
    Returns:
        str: Name of the next node to execute
    """
    intent = state.get("intent", "other")
    
    # Map intents to handler nodes
    intent_routing = {
        "faq": "faq",
        "order_create": "order",
        "order_update": "order_update",  # Now routes to dedicated order_update handler
        "complaint": "review",
        "review": "review",
        "other": "respond"
    }
    
    return intent_routing.get(intent, "respond")


def create_agent_workflow() -> StateGraph:
    """
    Create and configure the LangGraph agent workflow.
    
    This function builds the state graph with all nodes and edges,
    defining the conversation flow from intent classification through
    to final response generation.
    
    Returns:
        StateGraph: Compiled workflow graph ready for execution
    """
    # Initialize the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph
    workflow.add_node("classify", classify_intent)
    workflow.add_node("faq", handle_faq)
    workflow.add_node("order", handle_order)
    workflow.add_node("order_update", handle_order_update)  # New dedicated handler
    workflow.add_node("review", handle_review)
    workflow.add_node("respond", generate_response)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Add conditional edges from classify node based on intent
    workflow.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "faq": "faq",
            "order": "order",
            "order_update": "order_update",  # Route to dedicated handler
            "review": "review",
            "respond": "respond"
        }
    )
    
    # Add edges from handler nodes to response generator
    workflow.add_edge("faq", "respond")
    workflow.add_edge("order", "respond")
    workflow.add_edge("order_update", "respond")  # New edge
    workflow.add_edge("review", "respond")
    
    # Add edge from response generator to end
    workflow.add_edge("respond", END)
    
    return workflow


def compile_agent():
    """
    Compile the agent workflow for execution.
    
    Returns:
        Compiled agent ready to process conversations
    """
    workflow = create_agent_workflow()
    return workflow.compile()


# Create the compiled agent instance
agent = compile_agent()
