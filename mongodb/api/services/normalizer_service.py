"""
Normalizer Service - Chuẩn hóa dữ liệu bài báo
Đây là bước trung gian giữa Crawler và NLP Classifier
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dateutil import parser
import re
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class NormalizedArticle(BaseModel):
    """Schema cho bài báo đã chuẩn hóa"""
    url: str
    source: str
    title: str
    content: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    authors: List[str] = []
    category: Optional[str] = None
    tags: List[str] = []
    top_image: Optional[str] = None
    raw_data: Optional[Dict] = None
    normalized_at: datetime = datetime.now()


class NormalizerService:
    """
    Service chuẩn hóa dữ liệu bài báo từ nhiều nguồn khác nhau
    
    Flow:
    Crawler (RSS/Google News) -> Normalizer -> NLP Classifier -> MongoDB
    """
    
    def __init__(self):
        self.supported_sources = [
            'vnexpress.net',
            'tuoitre.vn',
            'dantri.com.vn',
            'vietnamnet.vn',
            'thanhnien.vn',
            'vtv.vn'
        ]
    
    def normalize_article(self, raw_article: Dict[str, Any]) -> NormalizedArticle:
        """
        Chuẩn hóa một bài báo từ raw data
        
        Args:
            raw_article: Dữ liệu thô từ crawler
            
        Returns:
            NormalizedArticle: Bài báo đã chuẩn hóa
        """
        try:
            # Normalize title
            title = self._normalize_text(raw_article.get('title', ''))
            
            # Normalize content
            content = self._normalize_text(
                raw_article.get('text') or 
                raw_article.get('content') or 
                raw_article.get('description', '')
            )
            
            # Normalize summary
            summary = self._normalize_text(raw_article.get('summary', ''))
            
            # Parse and normalize date
            published_at = self._normalize_date(
                raw_article.get('publish_date') or 
                raw_article.get('published_date') or
                raw_article.get('published_at')
            )
            
            # Normalize source
            source = self._normalize_source(raw_article.get('source', ''))
            
            # Normalize authors
            authors = self._normalize_authors(raw_article.get('authors', []))
            
            # Normalize tags
            tags = self._normalize_tags(raw_article.get('tags', []))
            
            # Get URL
            url = raw_article.get('url', '')
            
            # Get category
            category = raw_article.get('category', '')
            
            # Get top image
            top_image = None
            media = raw_article.get('media', {})
            if isinstance(media, dict):
                top_image = media.get('top_image')
            elif isinstance(raw_article.get('top_image'), str):
                top_image = raw_article.get('top_image')
            
            return NormalizedArticle(
                url=url,
                source=source,
                title=title,
                content=content,
                summary=summary,
                published_at=published_at,
                authors=authors,
                category=category,
                tags=tags,
                top_image=top_image,
                raw_data=raw_article,
                normalized_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error normalizing article: {e}")
            raise
    
    def normalize_batch(self, raw_articles: List[Dict]) -> List[NormalizedArticle]:
        """Chuẩn hóa danh sách bài báo"""
        normalized = []
        for article in raw_articles:
            try:
                normalized.append(self.normalize_article(article))
            except Exception as e:
                logger.warning(f"Skipping article due to error: {e}")
                continue
        return normalized
    
    def _normalize_text(self, text: str) -> str:
        """Chuẩn hóa văn bản"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        
        # Remove special characters but keep Vietnamese
        text = re.sub(r'[^\w\s\u00C0-\u024F\u1EA0-\u1EF9.,!?;:\-]', '', text)
        
        return text.strip()
    
    def _normalize_date(self, date_str: Any) -> Optional[datetime]:
        """Chuẩn hóa ngày tháng"""
        if not date_str:
            return None
            
        if isinstance(date_str, datetime):
            return date_str
            
        try:
            return parser.parse(str(date_str))
        except Exception:
            return None
    
    def _normalize_source(self, source: str) -> str:
        """Chuẩn hóa tên nguồn"""
        if not source:
            return "unknown"
        
        # Remove www. and clean up
        source = source.lower().replace('www.', '')
        
        # Map to canonical names
        source_mapping = {
            'vnexpress.net': 'VNExpress',
            'tuoitre.vn': 'Tuổi Trẻ',
            'dantri.com.vn': 'Dân Trí',
            'vietnamnet.vn': 'VietnamNet',
            'thanhnien.vn': 'Thanh Niên',
            'vtv.vn': 'VTV'
        }
        
        return source_mapping.get(source, source)
    
    def _normalize_authors(self, authors: Any) -> List[str]:
        """Chuẩn hóa danh sách tác giả"""
        if not authors:
            return []
        
        if isinstance(authors, str):
            authors = [authors]
        
        # Clean and filter empty
        return [a.strip() for a in authors if a and a.strip()]
    
    def _normalize_tags(self, tags: Any) -> List[str]:
        """Chuẩn hóa tags"""
        if not tags:
            return []
        
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]
        
        # Clean, lowercase and filter
        return [t.strip().lower() for t in tags if t and t.strip()]
    
    def validate_article(self, article: NormalizedArticle) -> bool:
        """Kiểm tra bài báo hợp lệ"""
        # Must have title
        if not article.title or len(article.title) < 10:
            return False
        
        # Must have content
        if not article.content or len(article.content) < 50:
            return False
        
        # Must have URL
        if not article.url:
            return False
        
        return True
