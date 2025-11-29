"""Integration tests for network insights generation

Tests the complete flow with real database interactions:
1. Aggregates data from tenant_stats across all tenants
2. Detects correlations between business type, day of week, hour, and products
3. Generates insights with confidence scores
4. Stores in demand_signals table
5. Ensures privacy by not exposing individual tenant identifiable information
"""

import pytest
from datetime import datetime, timedelta, date
from database import get_supabase_client
from stats_aggregator import StatsAggregator


class TestNetworkInsightsIntegration:
    """Integration tests for network insights with real database"""
    
    @pytest.fixture
    def client(self):
        """Get Supabase client"""
        return get_supabase_client()
    
    @pytest.fixture
    def aggregator(self, client):
        """Create StatsAggregator instance"""
        return StatsAggregator(client)
    
    def test_generate_insights_with_real_data(self, aggregator, client):
        """Test generating insights with real database data"""
        # Ensure we have some stats data
        stats_result = client.table("tenant_stats").select("*").limit(1).execute()
        
        if not stats_result.data:
            pytest.skip("No tenant stats data available for testing")
        
        # Generate insights
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        # Verify insights were generated and stored
        assert isinstance(insights, list), "Should return a list of insights"
        
        if len(insights) > 0:
            # Verify structure of first insight
            insight = insights[0]
            assert "pattern_type" in insight or "id" in insight
    
    def test_insights_stored_in_database(self, aggregator, client):
        """Test that insights are properly stored in demand_signals table"""
        # Generate insights
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        if len(insights) == 0:
            pytest.skip("No insights generated")
        
        # Query demand_signals table
        signals_result = client.table("demand_signals")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        
        assert len(signals_result.data) > 0, "Should have stored signals in database"
        
        # Verify structure
        signal = signals_result.data[0]
        assert "pattern_type" in signal
        assert "description" in signal
        assert "confidence_score" in signal
        assert "metadata" in signal
    
    def test_privacy_compliance(self, aggregator, client):
        """Test that insights don't expose tenant IDs or identifiable information"""
        # Generate insights
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        if len(insights) == 0:
            pytest.skip("No insights generated")
        
        # Get all tenant IDs
        tenants_result = client.table("tenants").select("id, name").execute()
        tenant_ids = [t["id"] for t in tenants_result.data]
        tenant_names = [t["name"] for t in tenants_result.data]
        
        # Check recent demand signals
        signals_result = client.table("demand_signals")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        
        for signal in signals_result.data:
            description = signal.get("description", "")
            metadata = signal.get("metadata", {})
            
            # Verify no tenant IDs in description
            for tenant_id in tenant_ids:
                assert tenant_id not in description, \
                    f"Description should not contain tenant ID {tenant_id}"
            
            # Verify no tenant names in description (they might be okay in aggregate)
            # But tenant_id field should never appear
            assert "tenant_id" not in str(metadata), \
                "Metadata should not contain tenant_id field"
    
    def test_cross_tenant_aggregation_real(self, aggregator, client):
        """Test that insights aggregate data from multiple tenants"""
        # Get count of active tenants
        tenants_result = client.table("tenants")\
            .select("id, type")\
            .eq("is_active", True)\
            .execute()
        
        if len(tenants_result.data) < 2:
            pytest.skip("Need at least 2 tenants for cross-tenant test")
        
        # Generate insights
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        if len(insights) == 0:
            pytest.skip("No insights generated")
        
        # Check that insights reference business types (not individual tenants)
        signals_result = client.table("demand_signals")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        
        business_types_found = set()
        for signal in signals_result.data:
            metadata = signal.get("metadata", {})
            if "business_type" in metadata:
                business_types_found.add(metadata["business_type"])
        
        # Should reference business types, not individual tenants
        assert len(business_types_found) > 0, \
            "Insights should reference business types"
    
    def test_confidence_scores_valid(self, aggregator, client):
        """Test that all confidence scores are in valid range [0, 1]"""
        # Generate insights
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        if len(insights) == 0:
            pytest.skip("No insights generated")
        
        # Check recent signals
        signals_result = client.table("demand_signals")\
            .select("confidence_score")\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        
        for signal in signals_result.data:
            confidence = float(signal["confidence_score"])
            assert 0 <= confidence <= 1, \
                f"Confidence score {confidence} must be between 0 and 1"
    
    def test_pattern_types_variety(self, aggregator, client):
        """Test that different pattern types are detected"""
        # Generate insights
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        if len(insights) == 0:
            pytest.skip("No insights generated")
        
        # Check pattern types
        signals_result = client.table("demand_signals")\
            .select("pattern_type")\
            .order("created_at", desc=True)\
            .limit(50)\
            .execute()
        
        pattern_types = set(s["pattern_type"] for s in signals_result.data)
        
        # Should have at least one pattern type
        assert len(pattern_types) > 0, "Should detect at least one pattern type"
        
        # Expected pattern types
        expected = ["business_type_peak_hour", "day_of_week_pattern", "product_category_hour"]
        found_expected = [p for p in expected if p in pattern_types]
        
        # Should find at least some expected patterns
        assert len(found_expected) > 0, \
            f"Should find expected pattern types. Found: {pattern_types}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
