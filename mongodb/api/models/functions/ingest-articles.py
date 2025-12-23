# mongodb/functions/ingest-articles.py
"""
Ingest articles function - MongoDB version
"""

import os
import sys
import json
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from crawl.database import get_db_manager

def ingest_articles_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle ingest articles request"""
    try:
        # Parse body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)

        articles = body.get('articles', [])
        if not articles:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'No articles provided'})
            }

        db_manager = get_db_manager()
        if not db_manager.initialize():
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Database connection failed'})
            }

        inserted_count = db_manager.insert_articles(articles)
        db_manager.close()

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': f'Successfully ingested {inserted_count} articles',
                'inserted_count': inserted_count
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
    test_articles = [
        {
            'title': 'Test Article',
            'content': 'Test content',
            'source': 'test',
            'url': 'http://example.com',
            'publish_date': '2025-12-23T00:00:00Z',
            'collected_at': '2025-12-23T12:00:00Z',
            'category': 'test',
            'severity': 'low'
        }
    ]
    test_event = {
        'body': json.dumps({'articles': test_articles})
    }
    result = ingest_articles_handler(test_event)
    print(json.dumps(result, indent=2, default=str))