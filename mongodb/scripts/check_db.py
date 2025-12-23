"""
Test script to verify MongoDB data and API
"""
from pymongo import MongoClient

def check_mongodb():
    """Check MongoDB data"""
    client = MongoClient("mongodb://localhost:27017")
    db = client["disaster_monitor"]
    
    print("=== MongoDB Stats ===")
    total = db.articles.count_documents({})
    disasters = db.articles.count_documents({"is_disaster": True})
    print(f"Total articles: {total}")
    print(f"Disaster articles: {disasters}")
    
    # Severity breakdown
    high = db.articles.count_documents({"severity": "high"})
    medium = db.articles.count_documents({"severity": "medium"})
    low = db.articles.count_documents({"severity": "low"})
    print(f"\nSeverity breakdown:")
    print(f"  High: {high}")
    print(f"  Medium: {medium}")
    print(f"  Low: {low}")
    
    # Sources
    sources = db.articles.distinct("source")
    print(f"\nSources ({len(sources)}): {sources}")
    
    # Sample disaster articles
    print("\n=== Sample Disaster Articles ===")
    for article in db.articles.find({"is_disaster": True}).limit(3):
        print(f"- {article.get('title', 'No title')[:60]}...")
        print(f"  Type: {article.get('disaster_type')}, Severity: {article.get('severity')}")
        print(f"  Keywords: {article.get('matched_keywords', [])[:5]}")
    
    client.close()


if __name__ == "__main__":
    check_mongodb()
