"""Stats Aggregation Service

This module provides functionality to aggregate tenant statistics from conversations,
messages, and orders into the tenant_stats table for analytics and insights.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta, timezone
from supabase import Client
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)


class StatsAggregator:
    """Service for aggregating tenant statistics
    
    Calculates interactions_count, orders_count, and top_product_id
    for each tenant by date and hour, storing results in tenant_stats table.
    """
    
    def __init__(self, client: Client):
        self.client = client
    
    def aggregate_tenant_stats(
        self, 
        tenant_id: str, 
        target_date: date, 
        hour: int
    ) -> Dict[str, Any]:
        """Aggregate statistics for a specific tenant, date, and hour
        
        Args:
            tenant_id: The tenant to aggregate stats for
            target_date: The date to aggregate
            hour: The hour (0-23) to aggregate
            
        Returns:
            Dictionary with aggregated stats
            
        Raises:
            ValueError: If hour is not in range 0-23
        """
        if not 0 <= hour <= 23:
            raise ValueError(f"Hour must be between 0 and 23, got {hour}")
        
        # Calculate time range for this hour
        start_time = datetime.combine(target_date, datetime.min.time()).replace(hour=hour)
        end_time = start_time + timedelta(hours=1)
        
        # Convert to ISO format for database queries
        start_iso = start_time.isoformat()
        end_iso = end_time.isoformat()
        
        # Count interactions (messages from users in this time period)
        interactions_count = self._count_interactions(tenant_id, start_iso, end_iso)
        
        # Count orders created in this time period
        orders_count = self._count_orders(tenant_id, start_iso, end_iso)
        
        # Find top product mentioned in this time period
        top_product_id = self._find_top_product(tenant_id, start_iso, end_iso)
        
        # Insert or update tenant_stats
        stats_data = {
            "tenant_id": tenant_id,
            "date": target_date.isoformat(),
            "hour": hour,
            "interactions_count": interactions_count,
            "orders_count": orders_count,
            "top_product_id": top_product_id
        }
        
        # Try to upsert (insert or update if exists)
        result = self._upsert_stats(stats_data)
        
        logger.info(
            f"Aggregated stats for tenant {tenant_id} on {target_date} hour {hour}: "
            f"{interactions_count} interactions, {orders_count} orders"
        )
        
        return result
    
    def _count_interactions(self, tenant_id: str, start_iso: str, end_iso: str) -> int:
        """Count user messages in the time period for a tenant"""
        # Get conversations for this tenant
        conversations_result = self.client.table("conversations")\
            .select("id")\
            .eq("tenant_id", tenant_id)\
            .execute()
        
        if not conversations_result.data:
            return 0
        
        conversation_ids = [conv["id"] for conv in conversations_result.data]
        
        # Count messages from users in these conversations within time range
        messages_result = self.client.table("messages")\
            .select("id", count="exact")\
            .in_("conversation_id", conversation_ids)\
            .eq("sender", "user")\
            .gte("created_at", start_iso)\
            .lt("created_at", end_iso)\
            .execute()
        
        return messages_result.count or 0
    
    def _count_orders(self, tenant_id: str, start_iso: str, end_iso: str) -> int:
        """Count orders created in the time period for a tenant"""
        orders_result = self.client.table("orders")\
            .select("id", count="exact")\
            .eq("tenant_id", tenant_id)\
            .gte("created_at", start_iso)\
            .lt("created_at", end_iso)\
            .execute()
        
        return orders_result.count or 0
    
    def _find_top_product(
        self, 
        tenant_id: str, 
        start_iso: str, 
        end_iso: str
    ) -> Optional[str]:
        """Find the most mentioned product in messages during the time period
        
        Looks for product mentions in messages with intent 'faq' or 'order_create'
        """
        # Get conversations for this tenant
        conversations_result = self.client.table("conversations")\
            .select("id")\
            .eq("tenant_id", tenant_id)\
            .execute()
        
        if not conversations_result.data:
            return None
        
        conversation_ids = [conv["id"] for conv in conversations_result.data]
        
        # Get messages with faq or order intents in time range
        messages_result = self.client.table("messages")\
            .select("text")\
            .in_("conversation_id", conversation_ids)\
            .in_("intent", ["faq", "order_create"])\
            .gte("created_at", start_iso)\
            .lt("created_at", end_iso)\
            .execute()
        
        if not messages_result.data:
            return None
        
        # Get all products for this tenant
        products_result = self.client.table("products")\
            .select("id, name")\
            .eq("tenant_id", tenant_id)\
            .eq("is_active", True)\
            .execute()
        
        if not products_result.data:
            return None
        
        # Count product mentions in messages
        product_mentions = Counter()
        
        for message in messages_result.data:
            text_lower = message["text"].lower()
            for product in products_result.data:
                product_name_lower = product["name"].lower()
                # Simple substring matching
                if product_name_lower in text_lower:
                    product_mentions[product["id"]] += 1
        
        # Return the most mentioned product
        if product_mentions:
            return product_mentions.most_common(1)[0][0]
        
        return None
    
    def _upsert_stats(self, stats_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update stats record
        
        Uses Supabase upsert to handle conflicts on unique constraint
        """
        result = self.client.table("tenant_stats")\
            .upsert(stats_data, on_conflict="tenant_id,date,hour")\
            .execute()
        
        return result.data[0] if result.data else stats_data
    
    def aggregate_recent_stats(
        self, 
        tenant_id: str, 
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """Aggregate stats for recent hours for a tenant
        
        Args:
            tenant_id: The tenant to aggregate stats for
            hours_back: Number of hours to go back from now
            
        Returns:
            List of aggregated stats records
        """
        results = []
        now = datetime.now(timezone.utc)
        
        for i in range(hours_back):
            target_time = now - timedelta(hours=i)
            target_date = target_time.date()
            target_hour = target_time.hour
            
            try:
                stats = self.aggregate_tenant_stats(tenant_id, target_date, target_hour)
                results.append(stats)
            except Exception as e:
                logger.error(
                    f"Error aggregating stats for {tenant_id} "
                    f"on {target_date} hour {target_hour}: {e}"
                )
        
        return results
    
    def aggregate_all_tenants_recent(self, hours_back: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """Aggregate recent stats for all active tenants
        
        Args:
            hours_back: Number of hours to go back from now
            
        Returns:
            Dictionary mapping tenant_id to list of stats records
        """
        # Get all active tenants
        tenants_result = self.client.table("tenants")\
            .select("id")\
            .eq("is_active", True)\
            .execute()
        
        results = {}
        
        for tenant in tenants_result.data:
            tenant_id = tenant["id"]
            try:
                tenant_stats = self.aggregate_recent_stats(tenant_id, hours_back)
                results[tenant_id] = tenant_stats
                logger.info(f"Aggregated {len(tenant_stats)} stats records for tenant {tenant_id}")
            except Exception as e:
                logger.error(f"Error aggregating stats for tenant {tenant_id}: {e}")
                results[tenant_id] = []
        
        return results
    
    def generate_network_insights(
        self, 
        days_back: int = 7,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Generate network insights from aggregated data across all tenants
        
        Analyzes patterns across all tenants to detect correlations between:
        - Business type and peak hours
        - Day of week and product demand
        - Hour and business type activity
        
        Ensures privacy by not exposing individual tenant identifiable information.
        
        Args:
            days_back: Number of days to analyze (default 7)
            min_confidence: Minimum confidence score to include insight (default 0.6)
            
        Returns:
            List of generated insights with patterns and confidence scores
        """
        logger.info(f"Generating network insights for last {days_back} days")
        
        # Calculate date range
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days_back)
        
        # Fetch all tenant stats in the date range
        stats_result = self.client.table("tenant_stats")\
            .select("tenant_id, date, hour, interactions_count, orders_count, top_product_id")\
            .gte("date", start_date.isoformat())\
            .lte("date", end_date.isoformat())\
            .execute()
        
        if not stats_result.data or len(stats_result.data) == 0:
            logger.warning("No stats data found for network insights generation")
            return []
        
        # Fetch tenant information (types)
        tenants_result = self.client.table("tenants")\
            .select("id, type")\
            .eq("is_active", True)\
            .execute()
        
        tenant_types = {t["id"]: t["type"] for t in tenants_result.data}
        
        # Fetch product information
        products_result = self.client.table("products")\
            .select("id, category, tenant_id")\
            .execute()
        
        product_info = {p["id"]: {"category": p["category"], "tenant_id": p["tenant_id"]} 
                       for p in products_result.data}
        
        # Analyze patterns
        insights = []
        
        # Pattern 1: Business type peak hours correlation
        business_hour_insights = self._analyze_business_type_hours(
            stats_result.data, tenant_types, min_confidence
        )
        insights.extend(business_hour_insights)
        
        # Pattern 2: Day of week patterns by business type
        day_pattern_insights = self._analyze_day_patterns(
            stats_result.data, tenant_types, min_confidence
        )
        insights.extend(day_pattern_insights)
        
        # Pattern 3: Product category demand by hour
        product_hour_insights = self._analyze_product_hour_patterns(
            stats_result.data, product_info, tenant_types, min_confidence
        )
        insights.extend(product_hour_insights)
        
        # Store insights in demand_signals table
        stored_insights = []
        for insight in insights:
            try:
                stored = self._store_demand_signal(insight)
                stored_insights.append(stored)
            except Exception as e:
                logger.error(f"Error storing demand signal: {e}")
        
        logger.info(f"Generated and stored {len(stored_insights)} network insights")
        return stored_insights
    
    def _analyze_business_type_hours(
        self, 
        stats_data: List[Dict[str, Any]], 
        tenant_types: Dict[str, str],
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """Analyze peak hours by business type"""
        insights = []
        
        # Aggregate interactions by business type and hour
        type_hour_interactions = defaultdict(lambda: defaultdict(int))
        type_hour_counts = defaultdict(lambda: defaultdict(int))
        
        for stat in stats_data:
            tenant_id = stat["tenant_id"]
            if tenant_id not in tenant_types:
                continue
            
            business_type = tenant_types[tenant_id]
            hour = stat["hour"]
            interactions = stat["interactions_count"] or 0
            
            type_hour_interactions[business_type][hour] += interactions
            type_hour_counts[business_type][hour] += 1
        
        # Find peak hours for each business type
        for business_type, hour_data in type_hour_interactions.items():
            if not hour_data:
                continue
            
            total_interactions = sum(hour_data.values())
            if total_interactions == 0:
                continue
            
            # Find top 3 hours
            sorted_hours = sorted(hour_data.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for hour, interactions in sorted_hours:
                # Calculate confidence based on proportion of total interactions
                confidence = min(interactions / total_interactions * 3, 1.0)  # Scale up for top hours
                
                if confidence >= min_confidence:
                    # Format hour range
                    hour_end = (hour + 1) % 24
                    hour_range = f"{hour:02d}:00-{hour_end:02d}:00"
                    
                    insights.append({
                        "pattern_type": "business_type_peak_hour",
                        "description": f"High activity for {business_type} businesses during {hour_range}",
                        "confidence_score": round(confidence, 2),
                        "metadata": {
                            "business_type": business_type,
                            "hour": hour,
                            "hour_range": hour_range,
                            "relative_activity": round(interactions / total_interactions, 2)
                        }
                    })
        
        return insights
    
    def _analyze_day_patterns(
        self, 
        stats_data: List[Dict[str, Any]], 
        tenant_types: Dict[str, str],
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """Analyze patterns by day of week and business type"""
        insights = []
        
        # Aggregate by business type and day of week
        type_day_interactions = defaultdict(lambda: defaultdict(int))
        type_day_orders = defaultdict(lambda: defaultdict(int))
        
        for stat in stats_data:
            tenant_id = stat["tenant_id"]
            if tenant_id not in tenant_types:
                continue
            
            business_type = tenant_types[tenant_id]
            # Parse date and get day of week (0=Monday, 6=Sunday)
            stat_date = datetime.fromisoformat(stat["date"]).date()
            day_of_week = stat_date.weekday()
            
            interactions = stat["interactions_count"] or 0
            orders = stat["orders_count"] or 0
            
            type_day_interactions[business_type][day_of_week] += interactions
            type_day_orders[business_type][day_of_week] += orders
        
        # Analyze patterns
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for business_type, day_data in type_day_interactions.items():
            if not day_data:
                continue
            
            total_interactions = sum(day_data.values())
            if total_interactions == 0:
                continue
            
            # Find peak days
            sorted_days = sorted(day_data.items(), key=lambda x: x[1], reverse=True)[:2]
            
            for day_num, interactions in sorted_days:
                confidence = min(interactions / total_interactions * 2, 1.0)
                
                if confidence >= min_confidence:
                    day_name = day_names[day_num]
                    
                    insights.append({
                        "pattern_type": "day_of_week_pattern",
                        "description": f"Increased demand for {business_type} businesses on {day_name}",
                        "confidence_score": round(confidence, 2),
                        "metadata": {
                            "business_type": business_type,
                            "day_of_week": day_num,
                            "day_name": day_name,
                            "relative_activity": round(interactions / total_interactions, 2)
                        }
                    })
        
        return insights
    
    def _analyze_product_hour_patterns(
        self, 
        stats_data: List[Dict[str, Any]], 
        product_info: Dict[str, Dict[str, Any]],
        tenant_types: Dict[str, str],
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """Analyze product category demand patterns by hour"""
        insights = []
        
        # Aggregate by category and hour
        category_hour_mentions = defaultdict(lambda: defaultdict(int))
        
        for stat in stats_data:
            top_product_id = stat.get("top_product_id")
            if not top_product_id or top_product_id not in product_info:
                continue
            
            product = product_info[top_product_id]
            category = product.get("category")
            if not category:
                continue
            
            hour = stat["hour"]
            interactions = stat["interactions_count"] or 0
            
            category_hour_mentions[category][hour] += interactions
        
        # Find patterns
        for category, hour_data in category_hour_mentions.items():
            if not hour_data:
                continue
            
            total_mentions = sum(hour_data.values())
            if total_mentions < 5:  # Minimum threshold
                continue
            
            # Find peak hours for this category
            sorted_hours = sorted(hour_data.items(), key=lambda x: x[1], reverse=True)[:2]
            
            for hour, mentions in sorted_hours:
                confidence = min(mentions / total_mentions * 2, 1.0)
                
                if confidence >= min_confidence:
                    hour_end = (hour + 1) % 24
                    hour_range = f"{hour:02d}:00-{hour_end:02d}:00"
                    
                    insights.append({
                        "pattern_type": "product_category_hour",
                        "description": f"High demand for {category} products during {hour_range}",
                        "confidence_score": round(confidence, 2),
                        "metadata": {
                            "category": category,
                            "hour": hour,
                            "hour_range": hour_range,
                            "relative_demand": round(mentions / total_mentions, 2)
                        }
                    })
        
        return insights
    
    def _store_demand_signal(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """Store a demand signal in the database
        
        Args:
            insight: Dictionary with pattern_type, description, confidence_score, metadata
            
        Returns:
            Stored demand signal record
        """
        signal_data = {
            "pattern_type": insight["pattern_type"],
            "description": insight["description"],
            "confidence_score": insight["confidence_score"],
            "metadata": insight.get("metadata", {})
        }
        
        result = self.client.table("demand_signals")\
            .insert(signal_data)\
            .execute()
        
        return result.data[0] if result.data else signal_data
