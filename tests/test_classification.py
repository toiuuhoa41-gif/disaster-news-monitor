"""
Test Classification Service
"""

import pytest
from mongodb.api.services.classification_service import (
    ClassificationService,
    DISASTER_KEYWORDS,
    SEVERITY_INDICATORS,
    REGION_MAPPING
)


class TestClassificationService:
    """Test NLP classification service"""
    
    @pytest.fixture
    def classifier(self):
        return ClassificationService()
    
    def test_detect_disaster_keywords(self, classifier):
        """Test disaster keyword detection"""
        text = "Bão số 9 gây lũ lụt nghiêm trọng tại miền Trung"
        result = classifier.classify(text)
        
        assert result["is_disaster"] == True
        assert "weather" in result["disaster_types"] or "flood" in result["disaster_types"]
    
    def test_non_disaster_text(self, classifier):
        """Test non-disaster text classification"""
        text = "Đội tuyển Việt Nam giành chiến thắng trước Thái Lan"
        result = classifier.classify(text)
        
        assert result["is_disaster"] == False
        assert result["confidence"] < 0.5
    
    def test_severity_detection_high(self, classifier):
        """Test high severity detection"""
        text = "Bão số 9 cấp 5 khẩn cấp gây thiệt hại nghiêm trọng, nhiều người tử vong"
        result = classifier.classify(text)
        
        assert result["severity"] == "high"
    
    def test_severity_detection_medium(self, classifier):
        """Test medium severity detection"""
        text = "Mưa lớn gây ngập úng cục bộ, người dân được sơ tán"
        result = classifier.classify(text)
        
        assert result["severity"] in ["medium", "high"]
    
    def test_region_detection_central(self, classifier):
        """Test central region detection"""
        text = "Lũ lụt nghiêm trọng tại Đà Nẵng và Quảng Nam"
        result = classifier.classify(text)
        
        assert result["region"] == "central"
    
    def test_region_detection_north(self, classifier):
        """Test north region detection"""
        text = "Mưa lớn tại Hà Nội gây ngập úng nhiều tuyến phố"
        result = classifier.classify(text)
        
        assert result["region"] == "north"
    
    def test_region_detection_south(self, classifier):
        """Test south region detection"""
        text = "Triều cường dâng cao tại TP.HCM"
        result = classifier.classify(text)
        
        assert result["region"] == "south"
    
    def test_disaster_type_flood(self, classifier):
        """Test flood disaster type"""
        text = "Lũ quét ở Sơn La gây sạt lở đất nghiêm trọng"
        result = classifier.classify(text)
        
        assert "flood" in result["disaster_types"]
    
    def test_disaster_type_earthquake(self, classifier):
        """Test earthquake disaster type"""
        text = "Động đất mạnh 5.1 độ richter xảy ra tại Kon Tum"
        result = classifier.classify(text)
        
        assert "earthquake" in result["disaster_types"]
    
    def test_keywords_database_structure(self):
        """Test keywords database has correct structure"""
        for category, data in DISASTER_KEYWORDS.items():
            assert "keywords" in data
            assert "weight" in data
            assert isinstance(data["keywords"], list)
            assert len(data["keywords"]) > 0
    
    def test_region_mapping_coverage(self):
        """Test region mapping covers all regions"""
        required_regions = ["north", "central", "south"]
        for region in required_regions:
            assert region in REGION_MAPPING
            assert len(REGION_MAPPING[region]) > 0
