import pytest
from app.services.analysis_service import AnalysisService

class TestAnalysisService:
    def setup_method(self):
        self.analysis_service = AnalysisService()
    
    def test_analyze_sentiment_positive(self):
        """Test positive sentiment analysis"""
        text = "This video is amazing and very helpful!"
        sentiment = self.analysis_service._analyze_sentiment(text)
        assert sentiment == "positive"
    
    def test_analyze_sentiment_negative(self):
        """Test negative sentiment analysis"""
        text = "This video is terrible and confusing!"
        sentiment = self.analysis_service._analyze_sentiment(text)
        assert sentiment == "negative"
    
    def test_analyze_sentiment_neutral(self):
        """Test neutral sentiment analysis"""
        text = "This is a video about programming."
        sentiment = self.analysis_service._analyze_sentiment(text)
        assert sentiment == "neutral"
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        comments = [
            "This Python tutorial is great for beginners",
            "Love the Python examples and explanations",
            "Python programming made easy with this tutorial"
        ]
        keywords = self.analysis_service._extract_keywords(comments)
        assert "python" in [k.lower() for k in keywords]
        assert "tutorial" in [k.lower() for k in keywords]
    
    def test_calculate_sentiment_summary(self):
        """Test sentiment summary calculation"""
        sentiments = ["positive", "positive", "negative", "neutral"]
        summary = self.analysis_service._calculate_sentiment_summary(sentiments)
        
        assert summary.positive == 0.5
        assert summary.negative == 0.25
        assert summary.neutral == 0.25
    
    def test_extract_next_topic_ideas(self):
        """Test next topic ideas extraction"""
        comments = [
            "Can you explain how to use decorators in Python?",
            "Please make a tutorial on machine learning",
            "Would love to see a video about web scraping"
        ]
        topics = self.analysis_service._extract_next_topic_ideas(comments)
        assert len(topics) > 0
        assert any("decorator" in topic.lower() for topic in topics)