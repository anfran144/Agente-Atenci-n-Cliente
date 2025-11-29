"""Scheduled job for stats aggregation

This script can be run periodically (e.g., via cron, systemd timer, or task scheduler)
to aggregate statistics for all tenants.

Example cron entry (run every hour):
0 * * * * cd /path/to/backend && python scheduled_stats_job.py

Example systemd timer:
- Create /etc/systemd/system/stats-aggregation.service
- Create /etc/systemd/system/stats-aggregation.timer
- Enable with: systemctl enable --now stats-aggregation.timer

For development/testing, you can also run this manually:
python scheduled_stats_job.py
"""

import sys
import logging
from datetime import datetime
from database import get_supabase_client
from stats_aggregator import StatsAggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stats_aggregation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_stats_aggregation():
    """Run stats aggregation for all active tenants"""
    logger.info("=" * 60)
    logger.info("Starting scheduled stats aggregation job")
    logger.info("=" * 60)
    
    try:
        # Initialize
        client = get_supabase_client()
        aggregator = StatsAggregator(client)
        
        # Aggregate stats for the current hour for all tenants
        now = datetime.utcnow()
        current_date = now.date()
        current_hour = now.hour
        
        logger.info(f"Aggregating stats for {current_date} hour {current_hour}")
        
        # Get all active tenants
        tenants_result = client.table("tenants")\
            .select("id, name")\
            .eq("is_active", True)\
            .execute()
        
        if not tenants_result.data:
            logger.warning("No active tenants found")
            return
        
        success_count = 0
        error_count = 0
        
        # Aggregate for each tenant
        for tenant in tenants_result.data:
            tenant_id = tenant["id"]
            tenant_name = tenant["name"]
            
            try:
                stats = aggregator.aggregate_tenant_stats(
                    tenant_id, 
                    current_date, 
                    current_hour
                )
                
                logger.info(
                    f"✓ {tenant_name}: "
                    f"{stats['interactions_count']} interactions, "
                    f"{stats['orders_count']} orders"
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"✗ Error aggregating stats for {tenant_name}: {e}")
                error_count += 1
        
        logger.info("=" * 60)
        logger.info(f"Stats aggregation completed: {success_count} success, {error_count} errors")
        logger.info("=" * 60)
        
        if error_count > 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error in stats aggregation job: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_stats_aggregation()
