# mongodb/init_mongodb.py
"""
Initialize MongoDB database and collections for disaster news monitor
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def init_database():
    """Initialize MongoDB database with indexes"""
    try:
        uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        db_name = os.getenv('MONGODB_DB_NAME', 'disaster_news')

        client = MongoClient(uri)
        db = client[db_name]

        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {uri}")

        # Create collections if they don't exist
        collections = ['articles']

        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"📁 Created collection: {collection_name}")
            else:
                print(f"📁 Collection already exists: {collection_name}")

        # Create indexes for articles collection
        articles_collection = db.articles

        # Index for publish_date (descending for latest first)
        articles_collection.create_index([('publish_date', -1)])
        print("🔍 Created index on publish_date")

        # Index for source
        articles_collection.create_index([('source', 1)])
        print("🔍 Created index on source")

        # Index for category
        articles_collection.create_index([('category', 1)])
        print("🔍 Created index on category")

        # Index for severity
        articles_collection.create_index([('severity', 1)])
        print("🔍 Created index on severity")

        # Compound index for common queries
        articles_collection.create_index([
            ('source', 1),
            ('category', 1),
            ('severity', 1),
            ('publish_date', -1)
        ])
        print("🔍 Created compound index")

        # Unique index on URL to prevent duplicates
        articles_collection.create_index([('url', 1)], unique=True)
        print("🔍 Created unique index on url")

        print(f"🎉 Database '{db_name}' initialized successfully!")
        print(f"📊 Collections: {db.list_collection_names()}")

        client.close()

    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("Make sure MongoDB is running on localhost:27017")
        return False
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

    return True

if __name__ == '__main__':
    print("🚀 Initializing MongoDB database...")
    success = init_database()
    if success:
        print("✅ Initialization completed!")
    else:
        print("❌ Initialization failed!")
        sys.exit(1)