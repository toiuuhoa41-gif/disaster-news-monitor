# mongodb/functions/get-articles.py
"""
Get articles function - MongoDB version
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from crawl.database import get_db_manager

def get_articles_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get articles request"""
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        limit = int(query_params.get('limit', 50))
        offset = int(query_params.get('offset', 0))
        source = query_params.get('source')
        severity = query_params.get('severity')
        category = query_params.get('category')

        db_manager = get_db_manager()
        if not db_manager.initialize():
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Database connection failed'})
            }

        articles = db_manager.get_articles(limit, offset, source, severity, category)
        total_count = db_manager.get_article_count(source, severity, category)

        db_manager.close()

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'articles': articles,
                'total': total_count,
                'limit': limit,
                'offset': offset
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

if __name__ == '__main__':
    # Test locally
    test_event = {
        'queryStringParameters': {
            'limit': '50'
        }
    }
    result = get_articles_handler(test_event)
    print(json.dumps(result, indent=2, default=str))