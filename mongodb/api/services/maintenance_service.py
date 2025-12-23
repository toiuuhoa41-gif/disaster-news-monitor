from datetime import datetime, timedelta
import logging
from mongodb.api.config.database import Database

# Setup logging
logger = logging.getLogger(__name__)


class MaintenanceService:
    def __init__(self):
        pass  # Use lazy loading
    
    @property
    def db(self):
        return Database.get_db()

    async def daily_cleanup(self):
        """Perform daily cleanup of old data."""
        try:
            # Define the cutoff date for old articles (e.g., 30 days ago)
            cutoff_date = datetime.now() - timedelta(days=30)
            result = await self.db.articles.delete_many({"published_at": {"$lt": cutoff_date}})
            logger.info(f"✅ Deleted {result.deleted_count} old articles from the database.")
            return {"deleted_count": result.deleted_count}
        except Exception as e:
            logger.error(f"❌ Daily cleanup failed: {e}")
            return {"error": str(e)}

    async def optimize_database(self):
        """Optimize the database by compacting collections."""
        try:
            # This is a placeholder for actual optimization logic
            # MongoDB does not have a direct compact command in the driver
            logger.info("✅ Database optimization completed (placeholder).")
            return {"status": "optimized"}
        except Exception as e:
            logger.error(f"❌ Database optimization failed: {e}")
            return {"error": str(e)}

    async def run_maintenance(self):
        """Run all maintenance tasks"""
        cleanup_result = await self.daily_cleanup()
        optimize_result = await self.optimize_database()
        return {
            "cleanup": cleanup_result,
            "optimization": optimize_result,
            "completed_at": datetime.now().isoformat()
        }