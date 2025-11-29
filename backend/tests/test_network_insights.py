"""Unit tests for network insights generation

Tests that the generate_network_insights method:
1. Aggregates data from tenant_stats across all tenants (Req 6.1)
2. Detects correlations between business type, day of week, hour, and products (Req 6.2)
3. Generates insights with confidence scores (Req 6.3)
4. Stores in demand_signals table
5. Ensures privacy by not exposing individual tenant identifiable information (Req 6.4)
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, MagicMock, patch
from stats_aggregator import StatsAggregator


class TestNetworkInsights:
    """Test suite for network insights generation"""
    
    def test_generate_network_insights_basic(self):
        """Test basic network insights generation"""
        # Setup mock client
        mock_client = Mock()
        
        # Mock tenant_stats data
        mock_stats_data = [
            {
                "tenant_id": "tenant-1",
                "date": "2024-11-25",
                "hour": 18,
                "interactions_count": 50,
                "orders_count": 10,
                "top_product_id": "product-1"
            },
            {
                "tenant_id": "tenant-2",
                "date": "2024-11-25",
                "hour": 18,
                "interactions_count": 30,
                "orders_count": 5,
                "top_product_id": "product-2"
            }
        ]
        
        # Mock tenants data
        mock_tenants_data = [
            {"id": "tenant-1", "type": "restaurant"},
            {"id": "tenant-2", "type": "bakery"}
        ]
        
        # Mock products data
        mock_products_data = [
            {"id": "product-1", "category": "pizzas", "tenant_id": "tenant-1"},
            {"id": "product-2", "category": "bread", "tenant_id": "tenant-2"}
        ]
        
        # Setup mock responses
        mock_stats_result = Mock()
        mock_stats_result.data = mock_stats_data
        
        mock_tenants_result = Mock()
        mock_tenants_result.data = mock_tenants_data
        
        mock_products_result = Mock()
        mock_products_result.data = mock_products_data
        
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": "signal-1"}]
        
        # Configure mock client
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        def table_side_effect(table_name):
            if table_name == "tenant_stats":
                mock_table.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_stats_result
            elif table_name == "tenants":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_tenants_result
            elif table_name == "products":
                mock_table.select.return_value.execute.return_value = mock_products_result
            elif table_name == "demand_signals":
                mock_table.insert.return_value.execute.return_value = mock_insert_result
            return mock_table
        
        mock_client.table.side_effect = table_side_effect
        
        # Create aggregator and generate insights
        aggregator = StatsAggregator(mock_client)
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        # Verify insights were generated
        assert len(insights) > 0, "Should generate at least one insight"
        
        # Verify each insight has required fields
        for insight in insights:
            assert "id" in insight or "pattern_type" in insight
    
    def test_privacy_no_tenant_ids_in_insights(self):
        """Test that insights don't expose individual tenant IDs (Req 6.4)"""
        mock_client = Mock()
        
        # Mock data with tenant IDs
        mock_stats_data = [
            {
                "tenant_id": "secret-tenant-123",
                "date": "2024-11-25",
                "hour": 12,
                "interactions_count": 100,
                "orders_count": 20,
                "top_product_id": "product-1"
            }
        ]
        
        mock_tenants_data = [
            {"id": "secret-tenant-123", "type": "restaurant"}
        ]
        
        mock_products_data = [
            {"id": "product-1", "category": "pizzas", "tenant_id": "secret-tenant-123"}
        ]
        
        # Setup mocks
        mock_stats_result = Mock()
        mock_stats_result.data = mock_stats_data
        
        mock_tenants_result = Mock()
        mock_tenants_result.data = mock_tenants_data
        
        mock_products_result = Mock()
        mock_products_result.data = mock_products_data
        
        stored_signals = []
        
        def capture_insert(data):
            stored_signals.append(data)
            result = Mock()
            result.data = [data]
            return Mock(execute=Mock(return_value=result))
        
        mock_table = Mock()
        
        def table_side_effect(table_name):
            if table_name == "tenant_stats":
                mock_table.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_stats_result
            elif table_name == "tenants":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_tenants_result
            elif table_name == "products":
                mock_table.select.return_value.execute.return_value = mock_products_result
            elif table_name == "demand_signals":
                mock_table.insert.side_effect = capture_insert
            return mock_table
        
        mock_client.table.side_effect = table_side_effect
        
        # Generate insights
        aggregator = StatsAggregator(mock_client)
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        # Verify no tenant IDs in descriptions
        for signal in stored_signals:
            description = signal.get("description", "")
            assert "secret-tenant-123" not in description, \
                "Insight description should not contain tenant ID"
            assert "tenant_id" not in description.lower(), \
                "Insight description should not reference tenant_id"
            
            # Check metadata doesn't expose tenant_id
            metadata = signal.get("metadata", {})
            assert "tenant_id" not in metadata, \
                "Insight metadata should not contain tenant_id"
    
    def test_cross_tenant_aggregation(self):
        """Test that insights aggregate across all tenants (Req 6.1)"""
        mock_client = Mock()
        
        # Mock data from multiple tenants
        mock_stats_data = [
            {"tenant_id": "tenant-1", "date": "2024-11-25", "hour": 18, 
             "interactions_count": 50, "orders_count": 10, "top_product_id": "p1"},
            {"tenant_id": "tenant-2", "date": "2024-11-25", "hour": 18,
             "interactions_count": 40, "orders_count": 8, "top_product_id": "p2"},
            {"tenant_id": "tenant-3", "date": "2024-11-25", "hour": 18,
             "interactions_count": 30, "orders_count": 6, "top_product_id": "p3"},
        ]
        
        mock_tenants_data = [
            {"id": "tenant-1", "type": "restaurant"},
            {"id": "tenant-2", "type": "restaurant"},
            {"id": "tenant-3", "type": "bakery"}
        ]
        
        mock_products_data = [
            {"id": "p1", "category": "pizzas", "tenant_id": "tenant-1"},
            {"id": "p2", "category": "pizzas", "tenant_id": "tenant-2"},
            {"id": "p3", "category": "bread", "tenant_id": "tenant-3"}
        ]
        
        # Setup mocks
        mock_stats_result = Mock()
        mock_stats_result.data = mock_stats_data
        
        mock_tenants_result = Mock()
        mock_tenants_result.data = mock_tenants_data
        
        mock_products_result = Mock()
        mock_products_result.data = mock_products_data
        
        stored_signals = []
        
        def capture_insert(data):
            stored_signals.append(data)
            result = Mock()
            result.data = [data]
            return Mock(execute=Mock(return_value=result))
        
        mock_table = Mock()
        
        def table_side_effect(table_name):
            if table_name == "tenant_stats":
                mock_table.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_stats_result
            elif table_name == "tenants":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_tenants_result
            elif table_name == "products":
                mock_table.select.return_value.execute.return_value = mock_products_result
            elif table_name == "demand_signals":
                mock_table.insert.side_effect = capture_insert
            return mock_table
        
        mock_client.table.side_effect = table_side_effect
        
        # Generate insights
        aggregator = StatsAggregator(mock_client)
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        # Verify insights were generated from multiple tenants
        assert len(insights) > 0, "Should generate insights"
        
        # Check that business type patterns aggregate multiple tenants
        business_type_insights = [s for s in stored_signals 
                                  if s.get("pattern_type") == "business_type_peak_hour"]
        
        if business_type_insights:
            # Should have insights for restaurant type (aggregating tenant-1 and tenant-2)
            restaurant_insights = [s for s in business_type_insights 
                                  if s.get("metadata", {}).get("business_type") == "restaurant"]
            assert len(restaurant_insights) > 0, \
                "Should generate insights for restaurant type aggregating multiple tenants"
    
    def test_confidence_scores_in_range(self):
        """Test that all insights have confidence scores between 0 and 1 (Req 6.3)"""
        mock_client = Mock()
        
        mock_stats_data = [
            {"tenant_id": "t1", "date": "2024-11-25", "hour": 18,
             "interactions_count": 50, "orders_count": 10, "top_product_id": "p1"}
        ]
        
        mock_tenants_data = [{"id": "t1", "type": "restaurant"}]
        mock_products_data = [{"id": "p1", "category": "pizzas", "tenant_id": "t1"}]
        
        mock_stats_result = Mock()
        mock_stats_result.data = mock_stats_data
        
        mock_tenants_result = Mock()
        mock_tenants_result.data = mock_tenants_data
        
        mock_products_result = Mock()
        mock_products_result.data = mock_products_data
        
        stored_signals = []
        
        def capture_insert(data):
            stored_signals.append(data)
            result = Mock()
            result.data = [data]
            return Mock(execute=Mock(return_value=result))
        
        mock_table = Mock()
        
        def table_side_effect(table_name):
            if table_name == "tenant_stats":
                mock_table.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_stats_result
            elif table_name == "tenants":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_tenants_result
            elif table_name == "products":
                mock_table.select.return_value.execute.return_value = mock_products_result
            elif table_name == "demand_signals":
                mock_table.insert.side_effect = capture_insert
            return mock_table
        
        mock_client.table.side_effect = table_side_effect
        
        # Generate insights
        aggregator = StatsAggregator(mock_client)
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        # Verify all confidence scores are in valid range
        for signal in stored_signals:
            confidence = signal.get("confidence_score")
            assert confidence is not None, "Insight must have confidence_score"
            assert 0 <= confidence <= 1, \
                f"Confidence score {confidence} must be between 0 and 1"
    
    def test_pattern_types_detected(self):
        """Test that different pattern types are detected (Req 6.2)"""
        mock_client = Mock()
        
        # Create diverse data to trigger different pattern types
        mock_stats_data = []
        
        # Add data for business type peak hour pattern
        for hour in [18, 19, 20]:
            mock_stats_data.append({
                "tenant_id": "t1",
                "date": "2024-11-25",
                "hour": hour,
                "interactions_count": 50 if hour == 18 else 30,
                "orders_count": 10,
                "top_product_id": "p1"
            })
        
        # Add data for day of week pattern
        for day_offset in range(7):
            target_date = (date(2024, 11, 25) + timedelta(days=day_offset)).isoformat()
            mock_stats_data.append({
                "tenant_id": "t1",
                "date": target_date,
                "hour": 12,
                "interactions_count": 60 if day_offset == 5 else 20,  # Saturday peak
                "orders_count": 10,
                "top_product_id": "p1"
            })
        
        mock_tenants_data = [{"id": "t1", "type": "restaurant"}]
        mock_products_data = [{"id": "p1", "category": "pizzas", "tenant_id": "t1"}]
        
        mock_stats_result = Mock()
        mock_stats_result.data = mock_stats_data
        
        mock_tenants_result = Mock()
        mock_tenants_result.data = mock_tenants_data
        
        mock_products_result = Mock()
        mock_products_result.data = mock_products_data
        
        stored_signals = []
        
        def capture_insert(data):
            stored_signals.append(data)
            result = Mock()
            result.data = [data]
            return Mock(execute=Mock(return_value=result))
        
        mock_table = Mock()
        
        def table_side_effect(table_name):
            if table_name == "tenant_stats":
                mock_table.select.return_value.gte.return_value.lte.return_value.execute.return_value = mock_stats_result
            elif table_name == "tenants":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_tenants_result
            elif table_name == "products":
                mock_table.select.return_value.execute.return_value = mock_products_result
            elif table_name == "demand_signals":
                mock_table.insert.side_effect = capture_insert
            return mock_table
        
        mock_client.table.side_effect = table_side_effect
        
        # Generate insights
        aggregator = StatsAggregator(mock_client)
        insights = aggregator.generate_network_insights(days_back=7, min_confidence=0.5)
        
        # Verify different pattern types were detected
        pattern_types = set(s.get("pattern_type") for s in stored_signals)
        
        # Should detect at least business type and day patterns
        assert len(pattern_types) > 0, "Should detect at least one pattern type"
        
        expected_patterns = ["business_type_peak_hour", "day_of_week_pattern", "product_category_hour"]
        found_expected = [p for p in expected_patterns if p in pattern_types]
        
        assert len(found_expected) > 0, \
            f"Should detect expected pattern types. Found: {pattern_types}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
