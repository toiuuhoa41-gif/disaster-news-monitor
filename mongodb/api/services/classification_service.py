"""
NLP Classification Service - Phân loại bài báo thiên tai
Sử dụng kết hợp Rule-based và Machine Learning
"""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
import logging
import re

logger = logging.getLogger(__name__)


# =====================================================
# DISASTER KEYWORDS DATABASE
# =====================================================

DISASTER_KEYWORDS = {
    "weather": {
        "keywords": [
            "bão", "áp thấp nhiệt đới", "mưa lớn", "mưa to", "dông lốc",
            "giông bão", "mưa đá", "lốc xoáy", "gió mạnh", "rét đậm",
            "rét hại", "nắng nóng", "nắng gay gắt", "sấm sét"
        ],
        "weight": 1.0
    },
    "flood": {
        "keywords": [
            "lũ", "lụt", "lũ quét", "lũ lụt", "ngập úng", "ngập nặng",
            "ngập sâu", "nước dâng", "sạt lở", "sạt lở đất", "vỡ đê",
            "tràn đê", "xả lũ", "hồ thủy điện", "ngập đường"
        ],
        "weight": 1.2
    },
    "drought": {
        "keywords": [
            "hạn hán", "khô hạn", "thiếu nước", "hạn mặn", "xâm nhập mặn",
            "cháy rừng", "thiếu mưa", "nứt nẻ", "mất mùa", "chết khát"
        ],
        "weight": 1.0
    },
    "earthquake": {
        "keywords": [
            "động đất", "địa chấn", "rung chấn", "sóng thần", "núi lửa",
            "sụt lún", "nứt đất", "rung lắc"
        ],
        "weight": 1.5
    },
    "general": {
        "keywords": [
            "thiên tai", "thảm họa", "cứu hộ", "cứu nạn", "sơ tán",
            "di dời", "cảnh báo khẩn", "ứng phó", "khắc phục hậu quả",
            "thiệt hại", "tử vong", "mất tích", "bị thương", "cô lập"
        ],
        "weight": 0.8
    }
}

SEVERITY_INDICATORS = {
    "high": {
        "keywords": [
            "cấp 4", "cấp 5", "khẩn cấp", "nguy hiểm", "chết người",
            "tử vong", "mất tích", "thiệt hại nặng", "nghiêm trọng",
            "đặc biệt nguy hiểm", "siêu bão", "lũ lịch sử", "kỷ lục"
        ],
        "death_threshold": 1
    },
    "medium": {
        "keywords": [
            "cấp 3", "thiệt hại", "sơ tán", "di dời", "cảnh báo",
            "ảnh hưởng", "ngập", "hư hại"
        ],
        "death_threshold": 0
    },
    "low": {
        "keywords": [
            "cấp 1", "cấp 2", "nhẹ", "cục bộ", "dự báo",
            "có thể xảy ra", "nguy cơ"
        ],
        "death_threshold": 0
    }
}

REGION_MAPPING = {
    "north": [
        "hà nội", "hải phòng", "quảng ninh", "hải dương", "hưng yên",
        "thái bình", "hà nam", "nam định", "ninh bình", "vĩnh phúc",
        "bắc ninh", "bắc giang", "thái nguyên", "lạng sơn", "cao bằng",
        "bắc kạn", "hà giang", "tuyên quang", "lào cai", "yên bái",
        "điện biên", "lai châu", "sơn la", "hòa bình", "phú thọ",
        "miền bắc", "đồng bằng bắc bộ", "tây bắc", "đông bắc"
    ],
    "central": [
        "thanh hóa", "nghệ an", "hà tĩnh", "quảng bình", "quảng trị",
        "thừa thiên huế", "đà nẵng", "quảng nam", "quảng ngãi",
        "bình định", "phú yên", "khánh hòa", "ninh thuận", "bình thuận",
        "miền trung", "bắc trung bộ", "nam trung bộ", "duyên hải miền trung"
    ],
    "south": [
        "tp.hcm", "thành phố hồ chí minh", "hồ chí minh", "bình dương",
        "đồng nai", "bà rịa", "vũng tàu", "tây ninh", "bình phước",
        "long an", "tiền giang", "bến tre", "vĩnh long", "trà vinh",
        "đồng tháp", "an giang", "kiên giang", "cần thơ", "hậu giang",
        "sóc trăng", "bạc liêu", "cà mau", "miền nam", "đông nam bộ",
        "tây nam bộ", "đồng bằng sông cửu long"
    ],
    "highlands": [
        "kon tum", "gia lai", "đắk lắk", "đắk nông", "lâm đồng",
        "tây nguyên", "cao nguyên"
    ]
}


class ClassificationResult(BaseModel):
    """Kết quả phân loại bài báo"""
    is_disaster: bool
    disaster_type: str
    severity: str
    confidence: float
    region: Optional[str] = None
    matched_keywords: List[str] = []
    details: Dict[str, Any] = {}


class ClassificationService:
    """
    NLP Classification Service
    
    Kết hợp:
    1. Rule-based: Keyword matching với weight
    2. Pattern matching: Regex cho số liệu thiệt hại
    3. Severity detection: Dựa trên từ khóa và số liệu
    4. Region detection: Mapping địa phương
    """
    
    def __init__(self):
        self.disaster_keywords = DISASTER_KEYWORDS
        self.severity_indicators = SEVERITY_INDICATORS
        self.region_mapping = REGION_MAPPING
        
        # Compile regex patterns
        self.death_pattern = re.compile(
            r'(\d+)\s*(người)?\s*(chết|tử vong|thiệt mạng|mất mạng)',
            re.IGNORECASE
        )
        self.missing_pattern = re.compile(
            r'(\d+)\s*(người)?\s*(mất tích|bị cuốn trôi)',
            re.IGNORECASE
        )
        self.injured_pattern = re.compile(
            r'(\d+)\s*(người)?\s*(bị thương|bị đau)',
            re.IGNORECASE
        )
        self.house_pattern = re.compile(
            r'(\d+)\s*(căn)?\s*(nhà|hộ)?\s*(sập|đổ|hư hại|ngập|bị cuốn)',
            re.IGNORECASE
        )
    
    async def classify_article(self, title: str, content: str) -> ClassificationResult:
        """
        Phân loại bài báo sử dụng NLP
        
        Args:
            title: Tiêu đề bài báo
            content: Nội dung bài báo
            
        Returns:
            ClassificationResult: Kết quả phân loại
        """
        try:
            # Combine text for analysis
            full_text = f"{title} {content}".lower()
            
            # Step 1: Detect disaster type and keywords
            disaster_type, matched_keywords, type_score = self._detect_disaster_type(full_text)
            
            # Step 2: Check if is disaster article
            # Lowered threshold to 0.2 vì chỉ cần 1-2 keyword cũng đủ xác định là tin thiên tai
            is_disaster = type_score >= 0.2 or len(matched_keywords) >= 1
            
            # Step 3: Detect severity
            severity, severity_details = self._detect_severity(full_text)
            
            # Step 4: Detect region
            region = self._detect_region(full_text)
            
            # Step 5: Calculate confidence
            confidence = self._calculate_confidence(
                type_score, 
                len(matched_keywords),
                severity,
                region is not None
            )
            
            return ClassificationResult(
                is_disaster=is_disaster,
                disaster_type=disaster_type if is_disaster else "none",
                severity=severity if is_disaster else "none",
                confidence=round(confidence, 2),
                region=region,
                matched_keywords=matched_keywords,
                details=severity_details
            )
            
        except Exception as e:
            logger.error(f"Error during classification: {e}")
            return ClassificationResult(
                is_disaster=False,
                disaster_type="none",
                severity="none",
                confidence=0.0
            )
    
    def _detect_disaster_type(self, text: str) -> Tuple[str, List[str], float]:
        """Phát hiện loại thiên tai"""
        scores = {}
        matched = {}
        
        for dtype, config in self.disaster_keywords.items():
            keywords = config["keywords"]
            weight = config["weight"]
            matches = []
            
            for kw in keywords:
                if kw in text:
                    matches.append(kw)
            
            if matches:
                score = len(matches) * weight
                scores[dtype] = score
                matched[dtype] = matches
        
        if not scores:
            return "other", [], 0.0
        
        # Get type with highest score
        best_type = max(scores, key=scores.get)
        all_matched = []
        for m in matched.values():
            all_matched.extend(m)
        
        # Normalize score
        total_score = sum(scores.values())
        normalized_score = min(total_score / 5.0, 1.0)
        
        return best_type, list(set(all_matched)), normalized_score
    
    def _detect_severity(self, text: str) -> Tuple[str, Dict]:
        """Phát hiện mức độ nghiêm trọng"""
        details = {
            "deaths": 0,
            "missing": 0,
            "injured": 0,
            "houses_affected": 0,
            "severity_keywords": []
        }
        
        # Extract numbers
        death_match = self.death_pattern.search(text)
        if death_match:
            details["deaths"] = int(death_match.group(1))
        
        missing_match = self.missing_pattern.search(text)
        if missing_match:
            details["missing"] = int(missing_match.group(1))
        
        injured_match = self.injured_pattern.search(text)
        if injured_match:
            details["injured"] = int(injured_match.group(1))
        
        house_match = self.house_pattern.search(text)
        if house_match:
            details["houses_affected"] = int(house_match.group(1))
        
        # Check severity keywords
        for level, config in self.severity_indicators.items():
            for kw in config["keywords"]:
                if kw in text:
                    details["severity_keywords"].append(kw)
        
        # Determine severity
        if details["deaths"] >= 1 or details["missing"] >= 3:
            return "high", details
        
        # Check for high severity keywords
        high_keywords = self.severity_indicators["high"]["keywords"]
        if any(kw in text for kw in high_keywords):
            return "high", details
        
        if details["injured"] >= 5 or details["houses_affected"] >= 10:
            return "medium", details
        
        medium_keywords = self.severity_indicators["medium"]["keywords"]
        if any(kw in text for kw in medium_keywords):
            return "medium", details
        
        return "low", details
    
    def _detect_region(self, text: str) -> Optional[str]:
        """Phát hiện vùng miền"""
        for region, provinces in self.region_mapping.items():
            for province in provinces:
                if province in text:
                    return region
        return None
    
    def _calculate_confidence(
        self, 
        type_score: float, 
        keyword_count: int,
        severity: str,
        has_region: bool
    ) -> float:
        """Tính độ tin cậy của phân loại"""
        base_confidence = type_score
        
        # Bonus for more keywords
        keyword_bonus = min(keyword_count * 0.05, 0.2)
        
        # Bonus for detected severity
        severity_bonus = {"high": 0.1, "medium": 0.05, "low": 0.02}.get(severity, 0)
        
        # Bonus for detected region
        region_bonus = 0.05 if has_region else 0
        
        return min(base_confidence + keyword_bonus + severity_bonus + region_bonus, 1.0)
    
    async def classify_batch(self, articles: List[Dict]) -> List[ClassificationResult]:
        """Phân loại nhiều bài báo"""
        results = []
        for article in articles:
            title = article.get('title', '')
            content = article.get('content', '') or article.get('text', '')
            result = await self.classify_article(title, content)
            results.append(result)
        return results


class HybridClassificationService:
    """
    Hybrid Classification Service
    
    Combines:
    1. Rule-based classification (fast, explainable)
    2. ML-based classification (better generalization)
    
    Uses ensemble voting for final decision.
    """
    
    def __init__(self):
        self.rule_classifier = ClassificationService()
        self._ml_classifier = None
    
    @property
    def ml_classifier(self):
        """Lazy load ML classifier"""
        if self._ml_classifier is None:
            try:
                from mongodb.api.services.ml_classification_service import get_ml_classifier
                self._ml_classifier = get_ml_classifier()
            except Exception as e:
                logger.warning(f"ML classifier not available: {e}")
                self._ml_classifier = False  # Mark as unavailable
        return self._ml_classifier if self._ml_classifier else None
    
    async def classify_article(self, title: str, content: str) -> ClassificationResult:
        """
        Hybrid classification using both rule-based and ML.
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            ClassificationResult with combined confidence
        """
        # Get rule-based result
        rule_result = await self.rule_classifier.classify_article(title, content)
        
        # Get ML result if available
        ml_result = None
        if self.ml_classifier:
            try:
                full_text = f"{title} {content}"
                ml_result = self.ml_classifier.predict(full_text)
            except Exception as e:
                logger.warning(f"ML classification failed: {e}")
        
        # Combine results
        if ml_result:
            # Ensemble voting
            rule_is_disaster = rule_result.is_disaster
            ml_is_disaster = ml_result.get('is_disaster', False)
            
            # Both agree -> high confidence
            if rule_is_disaster == ml_is_disaster:
                confidence = (rule_result.confidence + ml_result.get('confidence', 0.5)) / 2
                confidence = min(confidence + 0.1, 1.0)  # Bonus for agreement
            else:
                # Disagree -> use the one with higher confidence
                if rule_result.confidence >= ml_result.get('confidence', 0.5):
                    confidence = rule_result.confidence * 0.9  # Slight penalty
                else:
                    confidence = ml_result.get('confidence', 0.5) * 0.9
                    # Override with ML if it's more confident
                    if ml_result.get('confidence', 0) > rule_result.confidence:
                        rule_result.is_disaster = ml_is_disaster
            
            rule_result.confidence = round(confidence, 2)
            rule_result.details['ml_result'] = {
                'category': ml_result.get('category'),
                'confidence': ml_result.get('confidence'),
                'method': ml_result.get('method')
            }
        
        return rule_result
    
    async def classify_batch(self, articles: List[Dict]) -> List[ClassificationResult]:
        """Classify multiple articles"""
        results = []
        for article in articles:
            title = article.get('title', '')
            content = article.get('content', '') or article.get('text', '')
            result = await self.classify_article(title, content)
            results.append(result)
        return results
    
    def get_classifier_info(self) -> Dict[str, Any]:
        """Get information about classifiers"""
        info = {
            'rule_based': True,
            'ml_available': self.ml_classifier is not None,
            'disaster_keywords': list(DISASTER_KEYWORDS.keys()),
            'severity_levels': list(SEVERITY_INDICATORS.keys()),
            'regions': list(REGION_MAPPING.keys())
        }
        
        if self.ml_classifier:
            info['ml_info'] = self.ml_classifier.get_model_info()
        
        return info