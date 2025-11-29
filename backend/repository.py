from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import Client

class Repository:
    """Base repository with tenant-aware queries
    
    All queries to multi-tenant tables automatically filter by tenant_id
    to ensure data isolation between tenants.
    """
    
    def __init__(self, client: Client):
        self.client = client
    
    # Tenant operations
    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        result = self.client.table("tenants").select("*").eq("id", tenant_id).execute()
        return result.data[0] if result.data else None
    
    def get_active_tenants(self) -> List[Dict[str, Any]]:
        """Get all active tenants"""
        result = self.client.table("tenants").select("*").eq("is_active", True).execute()
        return result.data
    
    # Product operations
    def get_products(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all active products for a tenant"""
        result = self.client.table("products").select("*").eq("tenant_id", tenant_id).eq("is_active", True).execute()
        return result.data
    
    # Inventory operations
    def get_inventory_item(self, tenant_id: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Get inventory item for a product"""
        result = self.client.table("inventory_items").select("*").eq("tenant_id", tenant_id).eq("product_id", product_id).execute()
        return result.data[0] if result.data else None
    
    # FAQ operations
    def get_faqs(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all FAQs for a tenant"""
        result = self.client.table("faqs").select("*").eq("tenant_id", tenant_id).execute()
        return result.data
    
    # Conversation operations
    def create_conversation(self, tenant_id: str, channel: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new conversation"""
        data = {
            "tenant_id": tenant_id,
            "channel": channel,
            "customer_id": customer_id,
            "started_at": datetime.utcnow().isoformat()
        }
        result = self.client.table("conversations").insert(data).execute()
        return result.data[0]
    
    def end_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """End a conversation"""
        data = {"ended_at": datetime.utcnow().isoformat()}
        result = self.client.table("conversations").update(data).eq("id", conversation_id).execute()
        return result.data[0] if result.data else None
    
    # Message operations
    def create_message(self, conversation_id: str, sender: str, text: str, intent: Optional[str] = None) -> Dict[str, Any]:
        """Create a new message"""
        data = {
            "conversation_id": conversation_id,
            "sender": sender,
            "text": text,
            "intent": intent,
            "created_at": datetime.utcnow().isoformat()
        }
        result = self.client.table("messages").insert(data).execute()
        return result.data[0]
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        result = self.client.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        return result.data
    
    # Order operations
    def create_order(self, tenant_id: str, conversation_id: str, total_amount: float, status: str = "pending") -> Dict[str, Any]:
        """Create a new order"""
        data = {
            "tenant_id": tenant_id,
            "conversation_id": conversation_id,
            "status": status,
            "total_amount": total_amount,
            "created_at": datetime.utcnow().isoformat()
        }
        result = self.client.table("orders").insert(data).execute()
        return result.data[0]
    
    def create_order_items(self, order_id: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create order items"""
        data = [
            {
                "order_id": order_id,
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"]
            }
            for item in items
        ]
        result = self.client.table("order_items").insert(data).execute()
        return result.data
    
    # Review operations
    def create_review(self, tenant_id: str, conversation_id: str, rating: int, comment: str, source: str, requires_attention: bool = False) -> Dict[str, Any]:
        """Create a review"""
        data = {
            "tenant_id": tenant_id,
            "conversation_id": conversation_id,
            "rating": rating,
            "comment": comment,
            "source": source,
            "requires_attention": requires_attention,
            "created_at": datetime.utcnow().isoformat()
        }
        result = self.client.table("reviews").insert(data).execute()
        return result.data[0]
    
    # Stats operations
    def get_tenant_stats(self, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tenant statistics ordered by date and hour"""
        result = self.client.table("tenant_stats")\
            .select("*")\
            .eq("tenant_id", tenant_id)\
            .order("date", desc=True)\
            .order("hour", desc=True)\
            .limit(limit)\
            .execute()
        return result.data
    
    def get_peak_hours(self, tenant_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get peak hours for a tenant ordered by interactions_count"""
        result = self.client.table("tenant_stats")\
            .select("hour, interactions_count")\
            .eq("tenant_id", tenant_id)\
            .order("interactions_count", desc=True)\
            .limit(limit)\
            .execute()
        return result.data
    
    def get_messages_by_intent(self, tenant_id: str, intents: List[str]) -> List[Dict[str, Any]]:
        """Get messages for a tenant filtered by intent"""
        # First get conversations for this tenant
        conversations_result = self.client.table("conversations")\
            .select("id")\
            .eq("tenant_id", tenant_id)\
            .execute()
        
        if not conversations_result.data:
            return []
        
        conversation_ids = [conv["id"] for conv in conversations_result.data]
        
        # Get messages with specified intents
        result = self.client.table("messages")\
            .select("*")\
            .in_("conversation_id", conversation_ids)\
            .in_("intent", intents)\
            .execute()
        
        return result.data
    
    def get_all_messages_for_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a tenant"""
        # First get conversations for this tenant
        conversations_result = self.client.table("conversations")\
            .select("id")\
            .eq("tenant_id", tenant_id)\
            .execute()
        
        if not conversations_result.data:
            return []
        
        conversation_ids = [conv["id"] for conv in conversations_result.data]
        
        # Get all messages
        result = self.client.table("messages")\
            .select("*")\
            .in_("conversation_id", conversation_ids)\
            .eq("sender", "user")\
            .execute()
        
        return result.data
    
    # Demand signals operations
    def get_demand_signals(self, limit: int = 50, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Get demand signals (network insights) ordered by confidence and recency
        
        Args:
            limit: Maximum number of signals to return
            min_confidence: Minimum confidence score to filter by
            
        Returns:
            List of demand signal records
        """
        result = self.client.table("demand_signals")\
            .select("*")\
            .gte("confidence_score", min_confidence)\
            .order("confidence_score", desc=True)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data

    # User operations
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all active users"""
        result = self.client.table("users").select("*").eq("is_active", True).execute()
        return result.data
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        result = self.client.table("users").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        result = self.client.table("users").select("*").eq("email", email).execute()
        return result.data[0] if result.data else None
    
    def create_user(self, name: str, email: str, phone: Optional[str] = None, preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new user"""
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "preferences": preferences or {},
            "created_at": datetime.utcnow().isoformat()
        }
        result = self.client.table("users").insert(data).execute()
        return result.data[0]
    
    # User preferences (learned) operations
    def get_user_preferences(self, user_id: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get learned preferences for a user"""
        query = self.client.table("user_preferences").select("*").eq("user_id", user_id)
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)
        result = query.order("confidence", desc=True).execute()
        return result.data
    
    def upsert_user_preference(self, user_id: str, tenant_id: str, preference_type: str, preference_value: str, confidence: float = 0.5) -> Dict[str, Any]:
        """Create or update a learned user preference"""
        # Check if preference exists
        existing = self.client.table("user_preferences")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("tenant_id", tenant_id)\
            .eq("preference_type", preference_type)\
            .eq("preference_value", preference_value)\
            .execute()
        
        if existing.data:
            # Update existing preference
            pref = existing.data[0]
            new_count = pref.get("learned_from_count", 1) + 1
            new_confidence = min(0.95, confidence + (new_count * 0.05))  # Increase confidence with more observations
            
            result = self.client.table("user_preferences")\
                .update({
                    "confidence": new_confidence,
                    "learned_from_count": new_count,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", pref["id"])\
                .execute()
            return result.data[0]
        else:
            # Create new preference
            data = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "preference_type": preference_type,
                "preference_value": preference_value,
                "confidence": confidence,
                "learned_from_count": 1,
                "created_at": datetime.utcnow().isoformat()
            }
            result = self.client.table("user_preferences").insert(data).execute()
            return result.data[0]
    
    # Conversation with user
    def create_conversation_with_user(self, tenant_id: str, user_id: str, channel: str = "web") -> Dict[str, Any]:
        """Create a new conversation associated with a user"""
        data = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "channel": channel,
            "started_at": datetime.utcnow().isoformat()
        }
        result = self.client.table("conversations").insert(data).execute()
        return result.data[0]
    
    def get_user_conversations(self, user_id: str, tenant_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations for a user"""
        query = self.client.table("conversations").select("*").eq("user_id", user_id)
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)
        result = query.order("started_at", desc=True).limit(limit).execute()
        return result.data
    
    def get_user_order_history(self, user_id: str, tenant_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get order history for a user"""
        # Get user's conversations
        conversations = self.get_user_conversations(user_id, tenant_id, limit=100)
        if not conversations:
            return []
        
        conversation_ids = [c["id"] for c in conversations]
        
        # Get orders from those conversations
        query = self.client.table("orders").select("*, order_items(*)").in_("conversation_id", conversation_ids)
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data

    # Conversation metadata operations (for maintaining state like order_draft)
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID including metadata"""
        result = self.client.table("conversations").select("*").eq("id", conversation_id).execute()
        return result.data[0] if result.data else None
    
    def update_conversation_metadata(self, conversation_id: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update conversation metadata (used to persist order_draft between calls)"""
        result = self.client.table("conversations")\
            .update({"metadata": metadata})\
            .eq("id", conversation_id)\
            .execute()
        return result.data[0] if result.data else None
    
    def get_conversation_metadata(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation metadata"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            return conversation.get("metadata", {}) or {}
        return {}

    # ============================================
    # CONTEXT ENRICHMENT - Para recomendaciones inteligentes
    # ============================================
    
    def get_top_products_by_orders(self, tenant_id: str, days: int = 7, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most ordered products for a tenant in the last N days
        
        Returns products ranked by number of times they were ordered.
        """
        from datetime import timedelta
        
        # Get orders from last N days
        since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        orders = self.client.table("orders")\
            .select("id")\
            .eq("tenant_id", tenant_id)\
            .gte("created_at", since_date)\
            .execute()
        
        if not orders.data:
            return []
        
        order_ids = [o["id"] for o in orders.data]
        
        # Get order items
        order_items = self.client.table("order_items")\
            .select("product_id, quantity")\
            .in_("order_id", order_ids)\
            .execute()
        
        if not order_items.data:
            return []
        
        # Count by product
        from collections import Counter
        product_counts = Counter()
        for item in order_items.data:
            product_counts[item["product_id"]] += item["quantity"]
        
        # Get top products with details
        top_product_ids = [p[0] for p in product_counts.most_common(limit)]
        
        if not top_product_ids:
            return []
        
        products = self.client.table("products")\
            .select("id, name, price, category")\
            .in_("id", top_product_ids)\
            .execute()
        
        # Add order count to each product
        result = []
        for p in products.data:
            p["order_count"] = product_counts[p["id"]]
            result.append(p)
        
        # Sort by order count
        result.sort(key=lambda x: x["order_count"], reverse=True)
        return result
    
    def get_popular_products_by_mentions(self, tenant_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get products most mentioned in conversations
        
        Analyzes messages to find which products are talked about most.
        """
        # Get all products for this tenant
        products = self.get_products(tenant_id)
        if not products:
            return []
        
        # Get all messages for this tenant
        messages = self.get_all_messages_for_tenant(tenant_id)
        if not messages:
            return products[:limit]  # Return first products if no messages
        
        # Count mentions
        from collections import Counter
        mention_counts = Counter()
        
        for product in products:
            product_name_lower = product["name"].lower()
            for message in messages:
                if product_name_lower in message["text"].lower():
                    mention_counts[product["id"]] += 1
        
        # Get top mentioned products
        top_ids = [p[0] for p in mention_counts.most_common(limit)]
        
        result = []
        for p in products:
            if p["id"] in top_ids:
                p["mention_count"] = mention_counts[p["id"]]
                result.append(p)
        
        result.sort(key=lambda x: x.get("mention_count", 0), reverse=True)
        return result if result else products[:limit]
    
    def get_tenant_insights(self, tenant_id: str) -> Dict[str, Any]:
        """Get aggregated insights for a tenant
        
        Returns peak hours, popular products, common questions.
        """
        insights = {
            "peak_hours": [],
            "top_products": [],
            "total_orders": 0,
            "total_conversations": 0,
            "avg_rating": None
        }
        
        # Peak hours from stats
        stats = self.get_tenant_stats(tenant_id, limit=168)  # Last week
        if stats:
            from collections import Counter
            hour_counts = Counter()
            for s in stats:
                hour_counts[s["hour"]] += s.get("interactions_count", 0)
            insights["peak_hours"] = [{"hour": h, "count": c} for h, c in hour_counts.most_common(3)]
        
        # Top products
        insights["top_products"] = self.get_top_products_by_orders(tenant_id, days=30, limit=3)
        
        # Total orders
        orders = self.client.table("orders").select("id").eq("tenant_id", tenant_id).execute()
        insights["total_orders"] = len(orders.data) if orders.data else 0
        
        # Total conversations
        convs = self.client.table("conversations").select("id").eq("tenant_id", tenant_id).execute()
        insights["total_conversations"] = len(convs.data) if convs.data else 0
        
        # Average rating
        reviews = self.client.table("reviews").select("rating").eq("tenant_id", tenant_id).execute()
        if reviews.data:
            ratings = [r["rating"] for r in reviews.data]
            insights["avg_rating"] = round(sum(ratings) / len(ratings), 1)
        
        return insights
    
    def get_enriched_context(self, tenant_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get full enriched context for LLM
        
        This is the main method that aggregates all context for intelligent responses.
        """
        context = {
            "tenant_insights": self.get_tenant_insights(tenant_id),
            "top_products_week": self.get_top_products_by_orders(tenant_id, days=7, limit=5),
            "popular_products": self.get_popular_products_by_mentions(tenant_id, limit=5),
            "user_preferences": [],
            "user_order_history": [],
            "network_patterns": []
        }
        
        # User-specific context
        if user_id:
            context["user_preferences"] = self.get_user_preferences(user_id, tenant_id)
            context["user_order_history"] = self.get_user_order_history(user_id, tenant_id, limit=5)
        
        # Network patterns (cross-tenant insights)
        demand_signals = self.get_demand_signals(limit=5, min_confidence=0.6)
        context["network_patterns"] = [
            {"pattern": s.get("description", ""), "confidence": s.get("confidence_score", 0)}
            for s in demand_signals
        ]
        
        return context
