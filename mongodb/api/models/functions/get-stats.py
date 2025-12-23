# mongodb/functions/get-stats.py
"""
Get stats function - MongoDB version
"""

import os
import sys
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from crawl.database import get_db_manager

def get_stats_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get stats request"""
    try:
        db_manager = get_db_manager()
        if not db_manager.initialize():
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Database connection failed'})
            }

        stats = db_manager.get_stats()
        db_manager.close()

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(stats)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

if __name__ == '__main__':
    # Test locally
    test_event = {}
    result = get_stats_handler(test_event)
    print(json.dumps(result, indent=2, default=str))