from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from database import init_db, close_db, get_supabase_client
from repository import Repository

load_dotenv()

app = FastAPI(
    title="Multi-Tenant Customer Agent API",
    description="Multi-tenant conversational AI agent for customer service",
    version="1.0.0"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    init_db()
    print("[OK] Database connection initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    close_db()
    print("[OK] Database connection closed")

def get_repository() -> Repository:
    """Dependency injection for repository"""
    client = get_supabase_client()
    return Repository(client)

@app.get("/")
async def root():
    return {
        "message": "Multi-Tenant Customer Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health(repo: Repository = Depends(get_repository)):
    """Health check endpoint that verifies database connectivity"""
    try:
        # Test database connection by fetching tenants
        tenants = repo.get_active_tenants()
        return {
            "status": "healthy",
            "database": "connected",
            "active_tenants": len(tenants)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# Import models after app initialization to avoid circular imports
from models import TenantResponse, ChatRequest, ChatResponse, OrderSummary, StatsResponse, HourStat, ProductStat, CommonQuestion, NetworkInsightsResponse, GlobalPattern
from typing import List
from fastapi import HTTPException
from langchain_core.messages import HumanMessage, AIMessage
from collections import Counter
from stats_aggregator import StatsAggregator

@app.get("/tenants", response_model=List[TenantResponse])
async def get_tenants(repo: Repository = Depends(get_repository)):
    """Get all active tenants
    
    Returns a list of all active businesses on the platform.
    Requirement 9.1: Display available tenants for selection.
    """
    tenants = repo.get_active_tenants()
    return [
        TenantResponse(
            id=tenant["id"],
            name=tenant["name"],
            type=tenant["type"],
            is_active=tenant["is_active"]
        )
        for tenant in tenants
    ]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, repo: Repository = Depends(get_repository)):
    """Handle chat messages and return agent responses
    
    This endpoint:
    1. Validates tenant_id exists and is active (Requirement 8.3, 9.2)
    2. Creates or retrieves conversation with user context (Requirement 4.1)
    3. Retrieves user history and preferences for personalization
    4. Persists user message (Requirement 4.2)
    5. Invokes LangGraph agent with user context for processing
    6. Persists agent response (Requirement 4.2)
    7. Returns response with intent and metadata
    
    Requirements: 4.1, 4.2, 4.3, 8.3, 9.2, 9.3
    """
    try:
        # Validate tenant exists and is active (Requirement 8.3, 9.2)
        try:
            tenant = repo.get_tenant(request.tenant_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Tenant {request.tenant_id} not found")
        
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant {request.tenant_id} not found")
        if not tenant.get("is_active", False):
            raise HTTPException(status_code=403, detail=f"Tenant {request.tenant_id} is not active")
        
        # Get user info if user_id provided
        user_info = None
        user_preferences = []
        conversation_history = []
        order_history = []
        
        if request.user_id:
            # Get user details
            user_info = repo.get_user(request.user_id)
            if user_info:
                # Get user preferences for this tenant
                user_preferences = repo.get_user_preferences(request.user_id, request.tenant_id)
                
                # Get recent conversation history with this tenant
                conversation_history = repo.get_user_conversations(request.user_id, request.tenant_id, limit=5)
                
                # Get order history with this tenant
                order_history = repo.get_user_order_history(request.user_id, request.tenant_id, limit=5)
        
        # Create or retrieve conversation (Requirement 4.1)
        existing_order_draft = None
        if request.conversation_id:
            conversation_id = request.conversation_id
            # Retrieve existing order_draft from conversation metadata
            conversation_metadata = repo.get_conversation_metadata(conversation_id)
            existing_order_draft = conversation_metadata.get("order_draft")
        else:
            # Create new conversation with user_id if available
            if request.user_id and user_info:
                conversation = repo.create_conversation_with_user(
                    tenant_id=request.tenant_id,
                    user_id=request.user_id,
                    channel="web"
                )
            else:
                conversation = repo.create_conversation(
                    tenant_id=request.tenant_id,
                    channel="web",
                    customer_id=request.customer_id
                )
            conversation_id = conversation["id"]
        
        # Persist user message (Requirement 4.2)
        user_message = repo.create_message(
            conversation_id=conversation_id,
            sender="user",
            text=request.message,
            intent=None  # Intent will be classified by agent
        )
        
        # Build user context for personalization
        user_context = None
        if user_info:
            user_context = {
                "user_name": user_info.get("name", "").split()[0],  # First name
                "full_name": user_info.get("name", ""),
                "preferences": user_preferences,
                "recent_orders": order_history,
                "conversation_count": len(conversation_history),
                "is_returning_customer": len(conversation_history) > 0
            }
        
        # Prepare agent state with user context
        from agent import agent
        
        initial_state = {
            "tenant_id": request.tenant_id,
            "conversation_id": conversation_id,
            "messages": [HumanMessage(content=request.message)],
            "intent": None,
            "context": None,
            "order_draft": existing_order_draft,  # Restore order_draft from conversation metadata
            "requires_confirmation": False,
            "final_response": None,
            "user_context": user_context,  # Add user context for personalization
            "conversation_context": {}  # Initialize conversation context for tracking state
        }
        
        # Invoke LangGraph agent
        result = agent.invoke(initial_state)
        
        # Extract results from agent state
        intent = result.get("intent", "other")
        final_response = result.get("final_response", "I'm here to help! How can I assist you?")
        requires_confirmation = result.get("requires_confirmation", False)
        order_draft = result.get("order_draft")
        
        # Persist order_draft in conversation metadata to maintain state between calls
        # This ensures the order is not lost when user asks FAQ questions mid-order
        conversation_metadata = repo.get_conversation_metadata(conversation_id)
        conversation_metadata["order_draft"] = order_draft
        conversation_metadata["last_intent"] = intent
        repo.update_conversation_metadata(conversation_id, conversation_metadata)
        
        # Persist agent response (Requirement 4.2)
        agent_message = repo.create_message(
            conversation_id=conversation_id,
            sender="agent",
            text=final_response,
            intent=intent
        )
        
        # Prepare order summary if applicable
        order_summary = None
        if order_draft and requires_confirmation:
            order_summary = OrderSummary(
                products=order_draft.get("products", []),
                total=order_draft.get("total", 0.0)
            )
        
        # Return response (Requirement 9.3)
        return ChatResponse(
            conversation_id=conversation_id,
            response=final_response,
            intent=intent,
            requires_confirmation=requires_confirmation,
            order_summary=order_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/stats/{tenant_id}", response_model=StatsResponse)
async def get_stats(tenant_id: str, repo: Repository = Depends(get_repository)):
    """Get statistics for a specific tenant
    
    This endpoint:
    1. Calculates peak hours from tenant_stats ordered by interactions_count (Requirement 5.1)
    2. Calculates top products by counting mentions in messages (Requirement 5.2)
    3. Identifies common questions from messages table (Requirement 5.3)
    4. Returns StatsResponse with all metrics
    
    Requirements: 5.1, 5.2, 5.3
    """
    try:
        # Validate tenant exists
        tenant = repo.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
        
        # 1. Calculate peak hours from tenant_stats (Requirement 5.1)
        # Group by hour and sum interactions_count, then order by total count
        stats_data = repo.get_tenant_stats(tenant_id, limit=1000)
        
        # Aggregate interactions by hour
        hour_counts = Counter()
        for stat in stats_data:
            hour_counts[stat["hour"]] += stat.get("interactions_count", 0)
        
        # Get top 10 peak hours
        peak_hours = [
            HourStat(hour=hour, count=count)
            for hour, count in hour_counts.most_common(10)
        ]
        
        # 2. Calculate top products by counting mentions (Requirement 5.2)
        # Get messages with intent "faq" or "order_create"
        messages = repo.get_messages_by_intent(tenant_id, ["faq", "order_create"])
        
        # Get all products for this tenant
        products = repo.get_products(tenant_id)
        
        # Count product mentions in messages
        product_mentions = Counter()
        product_names = {}
        
        for product in products:
            product_names[product["id"]] = product["name"]
        
        for message in messages:
            text_lower = message["text"].lower()
            for product in products:
                product_name_lower = product["name"].lower()
                # Simple substring matching
                if product_name_lower in text_lower:
                    product_mentions[product["id"]] += 1
        
        # Get top 10 products
        top_products = [
            ProductStat(
                product_id=product_id,
                name=product_names.get(product_id, "Unknown"),
                mentions=count
            )
            for product_id, count in product_mentions.most_common(10)
        ]
        
        # 3. Identify common questions from messages (Requirement 5.3)
        # Get all user messages for this tenant
        all_messages = repo.get_all_messages_for_tenant(tenant_id)
        
        # Group similar questions by counting exact matches (simplified approach)
        # In production, you'd use NLP techniques for semantic similarity
        question_counts = Counter()
        
        for message in all_messages:
            # Normalize the question text
            question_text = message["text"].strip().lower()
            # Only count questions (messages ending with ?)
            if question_text.endswith("?"):
                question_counts[question_text] += 1
        
        # Get top 10 common questions
        common_questions = [
            CommonQuestion(question=question, frequency=count)
            for question, count in question_counts.most_common(10)
        ]
        
        # Return response
        return StatsResponse(
            tenant_id=tenant_id,
            peak_hours=peak_hours,
            top_products=top_products,
            common_questions=common_questions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Stats endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/network-insights", response_model=NetworkInsightsResponse)
async def get_network_insights(
    repo: Repository = Depends(get_repository),
    regenerate: bool = False,
    min_confidence: float = 0.6
):
    """Get network insights showing global patterns across all tenants
    
    This endpoint:
    1. Retrieves or generates global patterns from demand_signals table (Requirement 6.1)
    2. Returns insights with confidence scores (Requirement 6.3)
    3. Ensures privacy by not exposing individual tenant identifiable information (Requirement 6.4)
    
    Args:
        regenerate: If True, regenerate insights from current data. If False, retrieve stored insights.
        min_confidence: Minimum confidence score to include (default 0.6)
    
    Requirements: 6.1, 6.3
    """
    try:
        client = get_supabase_client()
        aggregator = StatsAggregator(client)
        
        # If regenerate is requested, generate new insights
        if regenerate:
            # Generate new insights (this will also store them in demand_signals)
            insights_data = aggregator.generate_network_insights(
                days_back=7,
                min_confidence=min_confidence
            )
        else:
            # Retrieve stored insights from demand_signals table
            insights_data = repo.get_demand_signals(limit=50, min_confidence=min_confidence)
        
        # Convert to GlobalPattern objects
        patterns = []
        for insight in insights_data:
            # Extract business types from metadata if available
            metadata = insight.get("metadata", {})
            business_types = None
            
            # Extract business type from metadata
            if "business_type" in metadata:
                business_types = [metadata["business_type"]]
            elif "business_types" in metadata:
                business_types = metadata["business_types"]
            
            pattern = GlobalPattern(
                pattern=insight.get("description", ""),
                confidence=float(insight.get("confidence_score", 0.0)),
                business_types=business_types
            )
            patterns.append(pattern)
        
        return NetworkInsightsResponse(patterns=patterns)
        
    except Exception as e:
        print(f"Network insights endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Import user models
from models import UserResponse, UserPreferenceResponse

@app.get("/users", response_model=List[UserResponse])
async def get_users(repo: Repository = Depends(get_repository)):
    """Get all active users
    
    Returns a list of all active users on the platform.
    """
    try:
        users = repo.get_users()
        return [
            UserResponse(
                id=user["id"],
                name=user["name"],
                email=user["email"],
                phone=user.get("phone"),
                preferences=user.get("preferences", {}),
                is_active=user.get("is_active", True)
            )
            for user in users
        ]
    except Exception as e:
        print(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, repo: Repository = Depends(get_repository)):
    """Get a specific user by ID"""
    try:
        user = repo.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            phone=user.get("phone"),
            preferences=user.get("preferences", {}),
            is_active=user.get("is_active", True)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/users/{user_id}/preferences", response_model=List[UserPreferenceResponse])
async def get_user_preferences(
    user_id: str, 
    tenant_id: str = None,
    repo: Repository = Depends(get_repository)
):
    """Get learned preferences for a user
    
    Returns preferences the system has learned from user interactions.
    Optionally filter by tenant_id.
    """
    try:
        user = repo.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        preferences = repo.get_user_preferences(user_id, tenant_id)
        return [
            UserPreferenceResponse(
                id=pref["id"],
                user_id=pref["user_id"],
                tenant_id=pref["tenant_id"],
                preference_type=pref["preference_type"],
                preference_value=pref["preference_value"],
                confidence=pref["confidence"],
                learned_from_count=pref["learned_from_count"]
            )
            for pref in preferences
        ]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user preferences error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/users/{user_id}/conversations")
async def get_user_conversations(
    user_id: str,
    tenant_id: str = None,
    limit: int = 10,
    repo: Repository = Depends(get_repository)
):
    """Get recent conversations for a user"""
    try:
        user = repo.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        conversations = repo.get_user_conversations(user_id, tenant_id, limit)
        return conversations
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user conversations error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/users/{user_id}/orders")
async def get_user_orders(
    user_id: str,
    tenant_id: str = None,
    limit: int = 10,
    repo: Repository = Depends(get_repository)
):
    """Get order history for a user"""
    try:
        user = repo.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        orders = repo.get_user_order_history(user_id, tenant_id, limit)
        return orders
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user orders error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
