"""
Script to import JSON data into MongoDB with NLP classification
"""
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pymongo import MongoClient
import asyncio

# Disaster keywords for classification
DISASTER_KEYWORDS = {
    'weather': ['bão', 'áp thấp nhiệt đới', 'siêu bão', 'gió mạnh', 'mưa lớn', 'mưa đá', 
                'ngập úng', 'triều cường', 'giông', 'lốc', 'sét đánh'],
    'flood': ['lũ', 'lụt', 'lũ quét', 'sạt lở', 'sạt lở đất', 'lở núi', 'vỡ đê', 
              'ngập lụt', 'lũ ống', 'nước dâng'],
    'drought': ['hạn hán', 'nắng nóng', 'khô hạn', 'thiếu nước', 'cháy rừng', 'nắng gắt'],
    'earthquake': ['động đất', 'rung chấn', 'chấn động', 'sóng thần'],
    'fire': ['cháy', 'hỏa hoạn', 'cháy lớn', 'cháy rừng', 'hỏa hoạn'],
    'general': ['thiên tai', 'thảm họa', 'cứu hộ', 'cứu nạn', 'sơ tán', 'di dời', 
                'cảnh báo khẩn', 'thiệt hại', 'mất tích', 'tử vong']
}

SEVERITY_KEYWORDS = {
    'high': ['chết', 'tử vong', 'mất tích', 'thiệt hại nặng', 'cấp 12', 'cấp 13', 
             'siêu bão', 'động đất mạnh', 'sạt lở nghiêm trọng', 'cảnh báo khẩn cấp'],
    'medium': ['bị thương', 'thiệt hại', 'ngập', 'sạt lở', 'gió mạnh', 'lũ quét', 'cháy'],
    'low': ['mưa lớn', 'gió', 'nắng nóng', 'khô hạn']
}

REGIONS = {
    'Miền Bắc': ['Hà Nội', 'Hải Phòng', 'Quảng Ninh', 'Lạng Sơn', 'Cao Bằng', 'Bắc Kạn',
                 'Thái Nguyên', 'Tuyên Quang', 'Hà Giang', 'Phú Thọ', 'Vĩnh Phúc', 'Bắc Giang',
                 'Bắc Ninh', 'Hải Dương', 'Hưng Yên', 'Thái Bình', 'Nam Định', 'Ninh Bình',
                 'Hòa Bình', 'Sơn La', 'Điện Biên', 'Lai Châu', 'Lào Cai', 'Yên Bái'],
    'Miền Trung': ['Thanh Hóa', 'Nghệ An', 'Hà Tĩnh', 'Quảng Bình', 'Quảng Trị', 'Huế',
                   'Đà Nẵng', 'Quảng Nam', 'Quảng Ngãi', 'Bình Định', 'Phú Yên', 'Khánh Hòa',
                   'Ninh Thuận', 'Bình Thuận', 'Kon Tum', 'Gia Lai', 'Đắk Lắk', 'Đắk Nông', 'Lâm Đồng'],
    'Miền Nam': ['TP HCM', 'Hồ Chí Minh', 'Bình Dương', 'Đồng Nai', 'Bà Rịa', 'Vũng Tàu',
                 'Long An', 'Tiền Giang', 'Bến Tre', 'Vĩnh Long', 'Trà Vinh', 'Cần Thơ',
                 'Hậu Giang', 'Sóc Trăng', 'Bạc Liêu', 'Cà Mau', 'An Giang', 'Kiên Giang', 'Đồng Tháp', 'Tây Ninh', 'Bình Phước']
}


def classify_article(title: str, content: str) -> dict:
    """Classify an article based on keywords"""
    text = f"{title} {content}".lower()
    
    # Check for disaster
    is_disaster = False
    disaster_type = None
    matched_keywords = []
    
    for dtype, keywords in DISASTER_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                is_disaster = True
                if not disaster_type:
                    disaster_type = dtype
                matched_keywords.append(kw)
    
    # Determine severity
    severity = 'low'
    for level in ['high', 'medium', 'low']:
        for kw in SEVERITY_KEYWORDS.get(level, []):
            if kw.lower() in text:
                severity = level
                break
        if severity != 'low':
            break
    
    # Determine region
    region = None
    for reg, provinces in REGIONS.items():
        for prov in provinces:
            if prov.lower() in text:
                region = reg
                break
        if region:
            break
    
    return {
        'is_disaster': is_disaster,
        'disaster_type': disaster_type,
        'severity': severity if is_disaster else None,
        'region': region,
        'matched_keywords': list(set(matched_keywords))[:10],
        'confidence': 0.8 if is_disaster else 0.0
    }


def import_json_to_mongodb(json_path: str, db_name: str = "disaster_monitor"):
    """Import JSON file to MongoDB"""
    
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db.articles
    
    print(f"Connected to MongoDB database: {db_name}")
    
    # Load JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    if not isinstance(articles, list):
        articles = [articles]
    
    print(f"Loaded {len(articles)} articles from {json_path}")
    
    processed = 0
    skipped = 0
    disaster_count = 0
    
    for article in articles:
        try:
            url = article.get("url", "")
            
            # Skip if already exists
            if collection.find_one({"url": url}):
                skipped += 1
                continue
            
            # Classify article
            title = article.get("title", "")
            content = article.get("text") or article.get("summary") or ""
            
            classification = classify_article(title, content)
            
            # Merge classification into article
            article.update(classification)
            
            if classification['is_disaster']:
                disaster_count += 1
            
            # Insert into MongoDB
            collection.insert_one(article)
            processed += 1
            
            if processed % 10 == 0:
                print(f"Processed: {processed}, Disasters: {disaster_count}, Skipped: {skipped}")
            
        except Exception as e:
            print(f"Error processing article: {e}")
            continue
    
    print(f"\n=== Import Complete ===")
    print(f"Total in file: {len(articles)}")
    print(f"Processed: {processed}")
    print(f"Disaster articles: {disaster_count}")
    print(f"Skipped (duplicates): {skipped}")
    print(f"Failed: {len(articles) - processed - skipped}")
    
    # Show collection stats
    total = collection.count_documents({})
    disasters = collection.count_documents({"is_disaster": True})
    print(f"\n=== MongoDB Stats ===")
    print(f"Total articles in DB: {total}")
    print(f"Disaster articles in DB: {disasters}")
    
    client.close()


if __name__ == "__main__":
    # Default JSON path
    json_path = "public/realtime_disaster_monitor_2025-12-23_07-34-16.json"
    
    # Check if path provided as argument
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    
    # Convert to absolute path if needed
    if not os.path.isabs(json_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(base_dir, json_path)
    
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        sys.exit(1)
    
    import_json_to_mongodb(json_path)
