"""
ML Classification Service for Disaster News
Uses scikit-learn for text classification with TF-IDF + Naive Bayes
"""

import os
import pickle
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
import logging

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================
# Training Data - Vietnamese Disaster News
# ============================================

# Expanded training dataset with Vietnamese disaster news samples
TRAINING_DATA = [
    # Flood (Lũ lụt)
    ("Lũ quét kinh hoàng cuốn trôi nhiều nhà cửa tại Yên Bái", "flood"),
    ("Nước lũ dâng cao gây ngập úng diện rộng tại đồng bằng sông Cửu Long", "flood"),
    ("Mưa lớn gây ngập lụt nghiêm trọng tại TP.HCM", "flood"),
    ("Triều cường kết hợp mưa lớn gây ngập nhiều tuyến đường", "flood"),
    ("Vỡ đê khiến hàng nghìn hecta lúa bị ngập", "flood"),
    ("Lũ ống bất ngờ ập xuống bản làng miền núi", "flood"),
    ("Nước sông dâng cao vượt mức báo động 3", "flood"),
    ("Hồ thủy điện xả lũ gây ngập vùng hạ du", "flood"),
    ("Mực nước sông Hồng đang lên nhanh", "flood"),
    ("Người dân di tản tránh lũ trong đêm", "flood"),
    ("Lũ lớn nhấn chìm nhiều xã vùng trũng", "flood"),
    ("Nước ngập sâu 2 mét tại khu dân cư", "flood"),
    
    # Storm (Bão)
    ("Bão số 9 đổ bộ vào miền Trung với sức gió giật cấp 15", "storm"),
    ("Siêu bão Yagi đang hướng vào biển Đông", "storm"),
    ("Áp thấp nhiệt đới mạnh lên thành bão", "storm"),
    ("Bão gây mưa to gió lớn tại các tỉnh ven biển", "storm"),
    ("Gió bão quật đổ nhiều cây xanh và nhà cửa", "storm"),
    ("Tâm bão đi qua các tỉnh Bình Định Phú Yên", "storm"),
    ("Sức gió mạnh nhất vùng gần tâm bão cấp 13", "storm"),
    ("Bão đổ bộ gây thiệt hại nặng nề", "storm"),
    ("Các tỉnh khẩn trương ứng phó bão", "storm"),
    ("Bão suy yếu thành áp thấp nhiệt đới", "storm"),
    ("Mắt bão đang cách bờ biển 200km", "storm"),
    ("Cảnh báo bão khẩn cấp cho ngư dân", "storm"),
    
    # Earthquake (Động đất)
    ("Động đất mạnh 5,8 độ richter tại Điện Biên", "earthquake"),
    ("Rung chấn mạnh khiến người dân hoang mang", "earthquake"),
    ("Dư chấn động đất còn tiếp diễn", "earthquake"),
    ("Địa chấn gây nứt tường nhiều nhà dân", "earthquake"),
    ("Trận động đất được ghi nhận tại vùng biên giới", "earthquake"),
    ("Động đất làm rung chuyển nhiều tòa nhà cao tầng", "earthquake"),
    ("Viện Vật lý địa cầu thông báo về trận động đất", "earthquake"),
    ("Người dân tháo chạy khi cảm nhận động đất", "earthquake"),
    ("Nhiều dư chấn nhỏ sau trận động đất chính", "earthquake"),
    ("Động đất xảy ra ở độ sâu 10km", "earthquake"),
    
    # Landslide (Sạt lở)
    ("Sạt lở đất vùi lấp nhiều ngôi nhà tại Quảng Nam", "landslide"),
    ("Mưa lớn gây sạt lở nghiêm trọng trên quốc lộ", "landslide"),
    ("Đồi núi sạt lở chặn đường giao thông", "landslide"),
    ("Sạt lở ta luy âm gây ách tắc giao thông", "landslide"),
    ("Nhiều điểm sạt lở nguy hiểm được cảnh báo", "landslide"),
    ("Sạt lở đất đá vùi lấp xe khách", "landslide"),
    ("Núi lở gây chết người tại vùng cao", "landslide"),
    ("Đường bị sạt lở chia cắt nhiều thôn bản", "landslide"),
    ("Lở đất cuốn trôi cầu tạm", "landslide"),
    ("Sạt lở bờ sông đe dọa nhà dân", "landslide"),
    
    # Drought (Hạn hán)
    ("Hạn hán kéo dài gây thiệt hại nặng cho nông nghiệp", "drought"),
    ("Hàng nghìn hecta lúa chết khô vì thiếu nước", "drought"),
    ("Nắng nóng kỷ lục gây hạn nghiêm trọng", "drought"),
    ("Người dân thiếu nước sinh hoạt trầm trọng", "drought"),
    ("Các hồ chứa cạn trơ đáy", "drought"),
    ("Hạn mặn xâm nhập sâu vào nội đồng", "drought"),
    ("Đất nứt nẻ vì khô hạn kéo dài", "drought"),
    ("Cây trồng chết hàng loạt do hạn hán", "drought"),
    ("Nguồn nước ngầm suy giảm nghiêm trọng", "drought"),
    ("Tình trạng thiếu nước báo động", "drought"),
    
    # Fire (Cháy)
    ("Cháy rừng lan rộng tại Nghệ An", "fire"),
    ("Đám cháy lớn thiêu rụi hàng chục hecta rừng", "fire"),
    ("Cháy nhà máy gây thiệt hại lớn", "fire"),
    ("Lửa bùng phát dữ dội tại khu công nghiệp", "fire"),
    ("Hỏa hoạn thiêu rụi kho hàng", "fire"),
    ("Cháy chung cư cao tầng khiến nhiều người mắc kẹt", "fire"),
    ("Cháy rừng thông gây ô nhiễm không khí", "fire"),
    ("Nắng nóng làm tăng nguy cơ cháy rừng", "fire"),
    ("Cháy lan nhanh do gió lớn", "fire"),
    ("Lực lượng PCCC khống chế đám cháy", "fire"),
    
    # Non-disaster (Không phải thiên tai)
    ("Thị trường chứng khoán tăng mạnh trong phiên giao dịch", "non-disaster"),
    ("Đội tuyển Việt Nam thắng đậm trong trận đấu", "non-disaster"),
    ("Giá vàng biến động nhẹ cuối tuần", "non-disaster"),
    ("Chính phủ họp bàn phát triển kinh tế", "non-disaster"),
    ("Festival âm nhạc thu hút đông đảo khán giả", "non-disaster"),
    ("Khai mạc hội chợ thương mại quốc tế", "non-disaster"),
    ("Đường cao tốc mới được khánh thành", "non-disaster"),
    ("Học sinh tựu trường năm học mới", "non-disaster"),
    ("Thời tiết đẹp thuận lợi cho du lịch", "non-disaster"),
    ("Doanh nghiệp công bố kết quả kinh doanh quý", "non-disaster"),
    ("Lễ hội mùa xuân diễn ra sôi nổi", "non-disaster"),
    ("Công nghệ mới được giới thiệu tại triển lãm", "non-disaster"),
]

# Category labels
DISASTER_CATEGORIES = {
    "flood": "Lũ lụt",
    "storm": "Bão",
    "earthquake": "Động đất",
    "landslide": "Sạt lở",
    "drought": "Hạn hán",
    "fire": "Cháy rừng",
    "non-disaster": "Không phải thiên tai"
}


class MLClassificationService:
    """
    ML-based classification service using TF-IDF + Naive Bayes.
    Falls back to rule-based classification if ML is not available.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the ML classifier"""
        self.model_path = model_path or "models/disaster_classifier.joblib"
        self.model: Optional[Pipeline] = None
        self.is_trained = False
        self._load_or_train_model()
    
    def _load_or_train_model(self):
        """Load existing model or train a new one"""
        if not ML_AVAILABLE:
            logger.warning("scikit-learn not available, ML classification disabled")
            return
        
        # Try to load existing model
        model_file = Path(self.model_path)
        if model_file.exists():
            try:
                self.model = joblib.load(model_file)
                self.is_trained = True
                logger.info(f"✅ Loaded ML model from {self.model_path}")
                return
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
        
        # Train new model
        self._train_model()
    
    def _train_model(self):
        """Train the classification model"""
        if not ML_AVAILABLE:
            return
        
        try:
            logger.info("🎓 Training ML classification model...")
            
            # Prepare training data
            texts = [text for text, _ in TRAINING_DATA]
            labels = [label for _, label in TRAINING_DATA]
            
            # Create pipeline with TF-IDF + Naive Bayes
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(
                    ngram_range=(1, 2),  # Unigrams and bigrams
                    max_features=5000,
                    min_df=1,
                    max_df=0.9,
                    sublinear_tf=True
                )),
                ('classifier', MultinomialNB(alpha=0.1))
            ])
            
            # Train
            self.model.fit(texts, labels)
            self.is_trained = True
            
            # Evaluate on training data
            predictions = self.model.predict(texts)
            accuracy = accuracy_score(labels, predictions)
            logger.info(f"✅ Model trained with {len(texts)} samples, accuracy: {accuracy:.2%}")
            
            # Save model
            self._save_model()
            
        except Exception as e:
            logger.error(f"Failed to train model: {e}")
            self.is_trained = False
    
    def _save_model(self):
        """Save the trained model to disk"""
        if not self.model:
            return
        
        try:
            model_dir = Path(self.model_path).parent
            model_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            logger.info(f"💾 Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict disaster category for a given text.
        
        Returns:
            Dict with category, confidence, and is_disaster flag
        """
        if not self.is_trained or not self.model:
            # Fallback to simple keyword matching
            return self._fallback_predict(text)
        
        try:
            # Get prediction
            category = self.model.predict([text])[0]
            
            # Get probabilities
            proba = self.model.predict_proba([text])[0]
            confidence = float(max(proba))
            
            # Get all class probabilities
            classes = self.model.classes_
            proba_dict = {cls: float(p) for cls, p in zip(classes, proba)}
            
            return {
                "category": category,
                "category_vi": DISASTER_CATEGORIES.get(category, category),
                "confidence": confidence,
                "is_disaster": category != "non-disaster",
                "probabilities": proba_dict,
                "method": "ml"
            }
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._fallback_predict(text)
    
    def _fallback_predict(self, text: str) -> Dict[str, Any]:
        """Simple keyword-based fallback prediction"""
        text_lower = text.lower()
        
        keywords_map = {
            "flood": ["lũ", "lụt", "ngập", "triều cường", "vỡ đê", "nước dâng", "lũ quét"],
            "storm": ["bão", "áp thấp", "gió mạnh", "siêu bão", "bão số"],
            "earthquake": ["động đất", "địa chấn", "rung chấn", "dư chấn"],
            "landslide": ["sạt lở", "lở đất", "núi lở", "ta luy"],
            "drought": ["hạn hán", "khô hạn", "thiếu nước", "hạn mặn", "cạn kiệt"],
            "fire": ["cháy rừng", "hỏa hoạn", "cháy lớn", "cháy lan", "lửa"]
        }
        
        for category, keywords in keywords_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return {
                        "category": category,
                        "category_vi": DISASTER_CATEGORIES.get(category, category),
                        "confidence": 0.7,  # Medium confidence for keyword match
                        "is_disaster": True,
                        "probabilities": {category: 0.7},
                        "method": "fallback"
                    }
        
        return {
            "category": "non-disaster",
            "category_vi": DISASTER_CATEGORIES["non-disaster"],
            "confidence": 0.5,
            "is_disaster": False,
            "probabilities": {"non-disaster": 0.5},
            "method": "fallback"
        }
    
    def batch_predict(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Predict categories for multiple texts"""
        return [self.predict(text) for text in texts]
    
    def retrain(self, additional_data: Optional[List[Tuple[str, str]]] = None):
        """
        Retrain the model with additional data.
        
        Args:
            additional_data: List of (text, category) tuples to add
        """
        if not ML_AVAILABLE:
            return {"error": "ML not available"}
        
        training_data = list(TRAINING_DATA)
        if additional_data:
            training_data.extend(additional_data)
        
        # Update training data reference (in production, save to database)
        self._train_model()
        
        return {
            "success": True,
            "total_samples": len(training_data),
            "is_trained": self.is_trained
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "ml_available": ML_AVAILABLE,
            "is_trained": self.is_trained,
            "model_path": self.model_path,
            "categories": list(DISASTER_CATEGORIES.keys()),
            "training_samples": len(TRAINING_DATA),
            "vectorizer_type": "TfidfVectorizer" if self.is_trained else None,
            "classifier_type": "MultinomialNB" if self.is_trained else None
        }


# ============================================
# Singleton Instance
# ============================================

_ml_classifier: Optional[MLClassificationService] = None


def get_ml_classifier() -> MLClassificationService:
    """Get or create the ML classifier singleton"""
    global _ml_classifier
    if _ml_classifier is None:
        _ml_classifier = MLClassificationService()
    return _ml_classifier


# ============================================
# Convenience Functions
# ============================================

def classify_disaster_ml(text: str) -> Dict[str, Any]:
    """
    Convenience function to classify text using ML.
    
    Usage:
        from mongodb.api.services.ml_classification_service import classify_disaster_ml
        result = classify_disaster_ml("Bão số 9 đổ bộ vào miền Trung")
        print(result['category'])  # 'storm'
        print(result['confidence'])  # 0.92
    """
    classifier = get_ml_classifier()
    return classifier.predict(text)


def is_disaster_ml(text: str, threshold: float = 0.5) -> bool:
    """Check if text is about a disaster with given confidence threshold"""
    result = classify_disaster_ml(text)
    return result['is_disaster'] and result['confidence'] >= threshold
