"""
Crawl Service - Thu thập tin tức thiên tai từ nhiều nguồn

Luồng dữ liệu:
1. Google News RSS (với từ khóa thiên tai) → Lọc bài viết liên quan
2. newspaper3k → Trích xuất nội dung đầy đủ
3. NLP Classifier → Phân loại và xác nhận thiên tai
4. MongoDB → Lưu trữ

Hỗ trợ:
- Google News RSS với các từ khóa thiên tai Việt Nam
- RSS feeds trực tiếp từ các báo
- Tự động phân loại severity và region
"""

import feedparser
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin
import logging
import re
from dataclasses import dataclass, field, asdict
import hashlib

from newspaper import Article as NewspaperArticle
from newspaper import Config as NewspaperConfig

from mongodb.api.config.database import Database
from mongodb.api.services.classification_service import ClassificationService

logger = logging.getLogger(__name__)


# =====================================================
# CONSTANTS & CONFIGURATION
# =====================================================

# Từ khóa thiên tai để tìm kiếm qua Google News
DISASTER_SEARCH_KEYWORDS = [
    # Weather disasters
    "bão Việt Nam", "lũ lụt Việt Nam", "ngập lụt", "sạt lở đất",
    "lũ quét", "áp thấp nhiệt đới", "mưa lớn ngập",
    # Earthquake & geological
    "động đất Việt Nam", "sụt lún đất",
    # Fire
    "cháy rừng Việt Nam", "cháy lớn", "hỏa hoạn",
    # Drought
    "hạn hán", "xâm nhập mặn", "thiếu nước",
    # General disaster terms
    "thiên tai Việt Nam", "cứu hộ cứu nạn", "sơ tán khẩn cấp",
    "thiệt hại do bão", "thiệt hại do lũ",
]

# Google News RSS URL template
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=vi&gl=VN&ceid=VN:vi"

# Các nguồn RSS trực tiếp từ báo Việt Nam
DIRECT_RSS_SOURCES = {
    "vnexpress": {
        "name": "VNExpress",
        "rss_urls": [
            "https://vnexpress.net/rss/thoi-su.rss",
            "https://vnexpress.net/rss/the-gioi.rss",
        ],
        "domain": "vnexpress.net"
    },
    "tuoitre": {
        "name": "Tuổi Trẻ",
        "rss_urls": [
            "https://tuoitre.vn/rss/thoi-su.rss",
            "https://tuoitre.vn/rss/the-gioi.rss",
        ],
        "domain": "tuoitre.vn"
    },
    "thanhnien": {
        "name": "Thanh Niên",
        "rss_urls": [
            "https://thanhnien.vn/rss/thoi-su.rss",
            "https://thanhnien.vn/rss/the-gioi.rss",
        ],
        "domain": "thanhnien.vn"
    },
    "dantri": {
        "name": "Dân Trí",
        "rss_urls": [
            "https://dantri.com.vn/rss/xa-hoi.rss",
            "https://dantri.com.vn/rss/the-gioi.rss",
        ],
        "domain": "dantri.com.vn"
    },
    "vietnamnet": {
        "name": "VietnamNet",
        "rss_urls": [
            "https://vietnamnet.vn/rss/thoi-su.rss",
        ],
        "domain": "vietnamnet.vn"
    },
    "vtv": {
        "name": "VTV",
        "rss_urls": [
            "https://vtv.vn/trong-nuoc.rss",
            "https://vtv.vn/the-gioi.rss",
        ],
        "domain": "vtv.vn"
    },
    "baotintuc": {
        "name": "Báo Tin Tức",
        "rss_urls": [
            "https://baotintuc.vn/xa-hoi.rss",
        ],
        "domain": "baotintuc.vn"
    },
    "nhandan": {
        "name": "Nhân Dân",
        "rss_urls": [
            "https://nhandan.vn/rss/xahoi-1335.rss",
        ],
        "domain": "nhandan.vn"
    },
    "nguoilaodong": {
        "name": "Người Lao Động",
        "rss_urls": [
            "https://nld.com.vn/thoi-su.rss",
        ],
        "domain": "nld.com.vn"
    },
    "24h": {
        "name": "24h",
        "rss_urls": [
            "https://cdn.24h.com.vn/upload/rss/tintuctrongngay.rss",
        ],
        "domain": "24h.com.vn"
    },
    "baomoi": {
        "name": "Báo Mới",
        "rss_urls": [
            "https://baomoi.com/xa-hoi.rss",
        ],
        "domain": "baomoi.com"
    },
    "chinhphu": {
        "name": "Báo Chính Phủ",
        "rss_urls": [
            "https://baochinhphu.vn/rss/home.rss",
        ],
        "domain": "baochinhphu.vn"
    },
    "hanoimoi": {
        "name": "Hà Nội Mới",
        "rss_urls": [
            "https://hanoimoi.vn/rss/xa-hoi-702.rss",
        ],
        "domain": "hanoimoi.vn"
    },
    "tienphong": {
        "name": "Tiền Phong",
        "rss_urls": [
            "https://tienphong.vn/rss/xa-hoi-2.rss",
        ],
        "domain": "tienphong.vn"
    },
}

# Newspaper3k configuration for Vietnamese
NEWSPAPER_CONFIG = NewspaperConfig()
NEWSPAPER_CONFIG.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
NEWSPAPER_CONFIG.request_timeout = 15
NEWSPAPER_CONFIG.language = 'vi'
NEWSPAPER_CONFIG.memoize_articles = False
NEWSPAPER_CONFIG.fetch_images = False


# =====================================================
# DATA CLASSES
# =====================================================

@dataclass
class RawArticle:
    """Bài báo thô từ RSS"""
    url: str
    title: str
    source: str
    published_date: Optional[datetime] = None
    summary: str = ""
    rss_source: str = ""  # google_news or direct_rss


@dataclass
class ExtractedArticle:
    """Bài báo đã trích xuất nội dung"""
    url: str
    title: str
    source: str
    text: str
    summary: str
    authors: List[str] = field(default_factory=list)
    publish_date: Optional[datetime] = None
    top_image: str = ""
    keywords: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.now)


@dataclass 
class ClassifiedArticle(ExtractedArticle):
    """Bài báo đã phân loại"""
    is_disaster: bool = False
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    confidence: float = 0.0
    region: Optional[str] = None
    matched_keywords: List[str] = field(default_factory=list)


# =====================================================
# CRAWL SERVICE
# =====================================================

class CrawlService:
    """
    Service thu thập và xử lý tin tức thiên tai
    
    Luồng:
    1. Fetch RSS (Google News + Direct sources)
    2. Filter potential disaster articles
    3. Extract full content with newspaper3k
    4. Classify with NLP
    5. Store in MongoDB
    """
    
    def __init__(self):
        self.classifier = ClassificationService()
        self.session: Optional[aiohttp.ClientSession] = None
        
    @property
    def db(self):
        return Database.get_db()
    
    @property
    def articles_collection(self):
        return self.db["articles"]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    # -------------------------------------------------
    # RSS FETCHING
    # -------------------------------------------------
    
    async def fetch_google_news_rss(self, keyword: str) -> List[RawArticle]:
        """
        Fetch articles from Google News RSS with disaster keyword
        
        Args:
            keyword: Từ khóa tìm kiếm (ví dụ: "bão Việt Nam")
            
        Returns:
            List of RawArticle from Google News
        """
        articles = []
        encoded_keyword = quote(keyword)
        url = GOOGLE_NEWS_RSS_URL.format(query=encoded_keyword)
        
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries[:20]:  # Limit 20 per keyword
                        # Extract actual URL from Google News redirect
                        actual_url = self._extract_google_news_url(entry.get('link', ''))
                        
                        if not actual_url:
                            continue
                        
                        raw = RawArticle(
                            url=actual_url,
                            title=entry.get('title', ''),
                            source=self._extract_source_from_title(entry.get('title', '')),
                            published_date=self._parse_date(entry.get('published', '')),
                            summary=entry.get('summary', ''),
                            rss_source='google_news'
                        )
                        articles.append(raw)
                        
                    logger.info(f"Fetched {len(articles)} articles from Google News for '{keyword}'")
                else:
                    logger.warning(f"Google News RSS returned {response.status} for '{keyword}'")
                    
        except Exception as e:
            logger.error(f"Error fetching Google News RSS for '{keyword}': {e}")
        
        return articles
    
    async def fetch_direct_rss(self, source_key: str) -> List[RawArticle]:
        """
        Fetch articles from direct RSS feed
        
        Args:
            source_key: Key from DIRECT_RSS_SOURCES (e.g., 'vnexpress')
            
        Returns:
            List of RawArticle
        """
        articles = []
        source_config = DIRECT_RSS_SOURCES.get(source_key)
        
        if not source_config:
            logger.warning(f"Unknown source: {source_key}")
            return articles
        
        for rss_url in source_config['rss_urls']:
            try:
                session = await self._get_session()
                async with session.get(rss_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        for entry in feed.entries[:30]:  # Limit 30 per feed
                            raw = RawArticle(
                                url=entry.get('link', ''),
                                title=entry.get('title', ''),
                                source=source_config['domain'],
                                published_date=self._parse_date(entry.get('published', '')),
                                summary=entry.get('summary', ''),
                                rss_source='direct_rss'
                            )
                            articles.append(raw)
                            
            except Exception as e:
                logger.error(f"Error fetching RSS from {rss_url}: {e}")
        
        logger.info(f"Fetched {len(articles)} articles from {source_config['name']}")
        return articles
    
    # -------------------------------------------------
    # CONTENT EXTRACTION
    # -------------------------------------------------
    
    async def extract_article_content(self, raw: RawArticle) -> Optional[ExtractedArticle]:
        """
        Extract full article content using newspaper3k
        
        Args:
            raw: RawArticle from RSS
            
        Returns:
            ExtractedArticle with full content, or None if failed
        """
        try:
            # Use newspaper3k to extract content
            article = NewspaperArticle(raw.url, config=NEWSPAPER_CONFIG)
            
            # Download and parse (run in executor for async)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, article.download)
            await loop.run_in_executor(None, article.parse)
            
            # Try NLP if available
            try:
                await loop.run_in_executor(None, article.nlp)
            except:
                pass  # NLP is optional
            
            extracted = ExtractedArticle(
                url=raw.url,
                title=article.title or raw.title,
                source=raw.source,
                text=article.text or "",
                summary=article.summary or raw.summary,
                authors=list(article.authors) if article.authors else [],
                publish_date=article.publish_date or raw.published_date,
                top_image=article.top_image or "",
                keywords=list(article.keywords) if article.keywords else [],
                meta={
                    'meta_description': article.meta_description,
                    'meta_keywords': article.meta_keywords,
                },
                collected_at=datetime.now()
            )
            
            return extracted
            
        except Exception as e:
            logger.warning(f"Failed to extract content from {raw.url}: {e}")
            
            # Fallback: use RSS data
            return ExtractedArticle(
                url=raw.url,
                title=raw.title,
                source=raw.source,
                text=raw.summary,  # Use summary as text
                summary=raw.summary,
                publish_date=raw.published_date,
                collected_at=datetime.now()
            )
    
    # -------------------------------------------------
    # CLASSIFICATION
    # -------------------------------------------------
    
    async def classify_article(self, extracted: ExtractedArticle) -> ClassifiedArticle:
        """
        Classify article using NLP service
        
        Args:
            extracted: ExtractedArticle with full content
            
        Returns:
            ClassifiedArticle with disaster classification
        """
        # Combine title and text for classification
        full_text = f"{extracted.title} {extracted.text}"
        
        # Use classification service
        result = await self.classifier.classify_article(
            title=extracted.title,
            content=extracted.text
        )
        
        # Create classified article
        classified = ClassifiedArticle(
            url=extracted.url,
            title=extracted.title,
            source=extracted.source,
            text=extracted.text,
            summary=extracted.summary,
            authors=extracted.authors,
            publish_date=extracted.publish_date,
            top_image=extracted.top_image,
            keywords=extracted.keywords,
            meta=extracted.meta,
            collected_at=extracted.collected_at,
            is_disaster=result.is_disaster,
            disaster_type=result.disaster_type,
            severity=result.severity,
            confidence=result.confidence,
            region=result.region,
            matched_keywords=result.matched_keywords
        )
        
        return classified
    
    # -------------------------------------------------
    # STORAGE
    # -------------------------------------------------
    
    async def store_article(self, article: ClassifiedArticle) -> bool:
        """
        Store classified article in MongoDB
        
        Args:
            article: ClassifiedArticle to store
            
        Returns:
            True if stored successfully, False if duplicate or error
        """
        try:
            # Check for duplicate
            existing = await self.articles_collection.find_one({"url": article.url})
            if existing:
                logger.debug(f"Duplicate article: {article.url}")
                return False
            
            # Convert to dict
            doc = asdict(article)
            
            # Add metadata
            doc['_id'] = self._generate_id(article.url)
            doc['created_at'] = datetime.now()
            
            # Convert datetime to string for MongoDB
            if doc.get('publish_date'):
                doc['publish_date'] = doc['publish_date'].isoformat() if isinstance(doc['publish_date'], datetime) else doc['publish_date']
            if doc.get('collected_at'):
                doc['collected_at'] = doc['collected_at'].isoformat() if isinstance(doc['collected_at'], datetime) else doc['collected_at']
            
            await self.articles_collection.insert_one(doc)
            logger.info(f"Stored article: {article.title[:50]}... (disaster={article.is_disaster})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article: {e}")
            return False
    
    # -------------------------------------------------
    # MAIN CRAWL METHODS
    # -------------------------------------------------
    
    async def crawl_google_news(self, max_keywords: int = 5) -> Dict[str, int]:
        """
        Crawl disaster news from Google News RSS
        
        Args:
            max_keywords: Maximum number of keywords to search
            
        Returns:
            Stats dict with counts
        """
        stats = {
            'total_fetched': 0,
            'extracted': 0,
            'disasters': 0,
            'stored': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        keywords = DISASTER_SEARCH_KEYWORDS[:max_keywords]
        all_raw_articles: Dict[str, RawArticle] = {}  # Dedupe by URL
        
        # Fetch from Google News for each keyword
        for keyword in keywords:
            raw_articles = await self.fetch_google_news_rss(keyword)
            for raw in raw_articles:
                if raw.url not in all_raw_articles:
                    all_raw_articles[raw.url] = raw
            
            await asyncio.sleep(1)  # Rate limiting
        
        stats['total_fetched'] = len(all_raw_articles)
        logger.info(f"Total unique articles from Google News: {len(all_raw_articles)}")
        
        # Process each article
        for url, raw in all_raw_articles.items():
            try:
                # Quick pre-filter: check title for disaster keywords
                if not self._quick_disaster_check(raw.title + " " + raw.summary):
                    continue
                
                # Extract full content
                extracted = await self.extract_article_content(raw)
                if not extracted or not extracted.text:
                    stats['errors'] += 1
                    continue
                stats['extracted'] += 1
                
                # Classify
                classified = await self.classify_article(extracted)
                
                # Only store disaster articles (or high confidence)
                if classified.is_disaster or classified.confidence > 0.3:
                    stats['disasters'] += 1
                    
                    stored = await self.store_article(classified)
                    if stored:
                        stats['stored'] += 1
                    else:
                        stats['duplicates'] += 1
                
                await asyncio.sleep(0.5)  # Be nice to servers
                
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                stats['errors'] += 1
        
        return stats
    
    async def crawl_direct_sources(self, sources: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Crawl from direct RSS sources
        
        Args:
            sources: List of source keys, or None for all
            
        Returns:
            Stats dict
        """
        stats = {
            'total_fetched': 0,
            'extracted': 0,
            'disasters': 0,
            'stored': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        source_keys = sources or list(DIRECT_RSS_SOURCES.keys())
        all_raw_articles: Dict[str, RawArticle] = {}
        
        # Fetch from each source
        for source_key in source_keys:
            raw_articles = await self.fetch_direct_rss(source_key)
            for raw in raw_articles:
                if raw.url not in all_raw_articles:
                    all_raw_articles[raw.url] = raw
            
            await asyncio.sleep(0.5)
        
        stats['total_fetched'] = len(all_raw_articles)
        logger.info(f"Total unique articles from direct sources: {len(all_raw_articles)}")
        
        # Process each article
        for url, raw in all_raw_articles.items():
            try:
                # Quick pre-filter
                if not self._quick_disaster_check(raw.title + " " + raw.summary):
                    continue
                
                # Extract content
                extracted = await self.extract_article_content(raw)
                if not extracted or not extracted.text:
                    stats['errors'] += 1
                    continue
                stats['extracted'] += 1
                
                # Classify
                classified = await self.classify_article(extracted)
                
                if classified.is_disaster or classified.confidence > 0.3:
                    stats['disasters'] += 1
                    
                    stored = await self.store_article(classified)
                    if stored:
                        stats['stored'] += 1
                    else:
                        stats['duplicates'] += 1
                
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                stats['errors'] += 1
        
        return stats
    
    async def crawl_all(self) -> Dict[str, Any]:
        """
        Full crawl from all sources
        
        Returns:
            Combined stats from all sources
        """
        logger.info("Starting full crawl from all sources...")
        start_time = datetime.now()
        
        try:
            # Crawl Google News
            google_stats = await self.crawl_google_news(max_keywords=10)
            
            # Crawl direct sources
            direct_stats = await self.crawl_direct_sources()
            
            # Combine stats
            combined_stats = {
                'google_news': google_stats,
                'direct_sources': direct_stats,
                'total': {
                    'fetched': google_stats['total_fetched'] + direct_stats['total_fetched'],
                    'extracted': google_stats['extracted'] + direct_stats['extracted'],
                    'disasters': google_stats['disasters'] + direct_stats['disasters'],
                    'stored': google_stats['stored'] + direct_stats['stored'],
                    'duplicates': google_stats['duplicates'] + direct_stats['duplicates'],
                    'errors': google_stats['errors'] + direct_stats['errors'],
                },
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"Full crawl completed: {combined_stats['total']}")
            return combined_stats
            
        finally:
            await self.close()
    
    # -------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------
    
    def _extract_google_news_url(self, google_url: str) -> Optional[str]:
        """Extract actual article URL from Google News redirect URL"""
        # Google News URLs look like: https://news.google.com/rss/articles/CBMi...
        # We need to decode the base64 encoded URL
        
        if not google_url:
            return None
        
        # If it's not a Google News URL, return as-is
        if 'news.google.com' not in google_url:
            return google_url
        
        try:
            # Try to extract URL from Google News redirect
            # Google News uses base64 encoded URLs in the path
            import base64
            
            # Method 1: Extract from URL parameter if present
            if 'url=' in google_url:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(google_url)
                params = parse_qs(parsed.query)
                if 'url' in params:
                    return params['url'][0]
            
            # Method 2: Decode base64 from path
            # URLs look like: /rss/articles/CBMi...
            if '/articles/' in google_url:
                path_part = google_url.split('/articles/')[-1]
                # Remove any query params
                path_part = path_part.split('?')[0]
                
                # Try different base64 decoding approaches
                for prefix in ['CBMi', 'CAIi']:
                    if path_part.startswith(prefix):
                        try:
                            # Add padding if needed
                            encoded = path_part[4:]  # Remove prefix
                            padding = 4 - len(encoded) % 4
                            if padding != 4:
                                encoded += '=' * padding
                            decoded = base64.urlsafe_b64decode(encoded)
                            # Find URL in decoded bytes
                            decoded_str = decoded.decode('utf-8', errors='ignore')
                            # Extract URL pattern
                            url_match = re.search(r'https?://[^\s"<>]+', decoded_str)
                            if url_match:
                                return url_match.group(0)
                        except:
                            pass
            
            # Fallback: return original Google URL (will redirect)
            return google_url
            
        except Exception as e:
            logger.debug(f"Could not extract URL from Google News: {e}")
            return google_url
    
    def _extract_source_from_title(self, title: str) -> str:
        """Extract source name from Google News title (usually at the end)"""
        # Google News titles format: "Article Title - Source Name"
        if ' - ' in title:
            parts = title.rsplit(' - ', 1)
            if len(parts) == 2:
                return parts[1].strip()
        return "unknown"
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string from RSS feed"""
        if not date_str:
            return None
        
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            pass
        
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            pass
        
        return None
    
    def _quick_disaster_check(self, text: str) -> bool:
        """
        Quick check if text might be about a disaster
        Used for pre-filtering before full extraction
        """
        text_lower = text.lower()
        
        quick_keywords = [
            'bão', 'lũ', 'lụt', 'ngập', 'sạt lở', 'động đất',
            'cháy', 'thiên tai', 'cứu hộ', 'sơ tán', 'thiệt hại',
            'mưa lớn', 'lốc', 'áp thấp', 'hạn hán', 'mất tích',
            'tử vong', 'cứu nạn', 'khẩn cấp', 'cảnh báo'
        ]
        
        return any(kw in text_lower for kw in quick_keywords)
    
    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()[:24]


# =====================================================
# DAILY CRAWL SERVICE (for scheduler)
# =====================================================

class DailyCrawlService:
    """Service for scheduled daily crawls"""
    
    def __init__(self):
        self.crawl_service = CrawlService()
    
    @property
    def db(self):
        return Database.get_db()
    
    async def crawl_all_sources(self) -> Dict[str, Any]:
        """
        Execute full daily crawl
        Called by scheduler at 00:05
        """
        logger.info("🌐 Starting daily crawl job...")
        
        try:
            stats = await self.crawl_service.crawl_all()
            
            # Store crawl stats
            await self._store_crawl_stats(stats)
            
            logger.info(f"✅ Daily crawl completed: {stats['total']['stored']} new articles")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Daily crawl failed: {e}")
            return {'error': str(e)}
    
    async def _store_crawl_stats(self, stats: Dict[str, Any]):
        """Store crawl statistics for monitoring"""
        try:
            collection = self.db['crawl_logs']
            await collection.insert_one({
                'type': 'daily_crawl',
                'stats': stats,
                'timestamp': datetime.now()
            })
        except Exception as e:
            logger.warning(f"Failed to store crawl stats: {e}")


# =====================================================
# CONVENIENCE FUNCTIONS
# =====================================================

async def run_crawl():
    """Standalone function to run a full crawl"""
    service = CrawlService()
    return await service.crawl_all()


if __name__ == "__main__":
    # Test crawl
    import asyncio
    
    async def test():
        service = CrawlService()
        
        # Test Google News
        print("Testing Google News RSS...")
        articles = await service.fetch_google_news_rss("bão Việt Nam")
        print(f"Found {len(articles)} articles")
        
        if articles:
            print(f"First article: {articles[0].title}")
        
        await service.close()
    
    asyncio.run(test())