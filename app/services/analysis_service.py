import re
import logging
import asyncio
from typing import List, Dict, Tuple
from collections import Counter
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from app.models import VideoAnalysis, Comment, SentimentSummary, BatchProcessingStatus

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'this', 'that', 'these', 'those', 'i', 'me',
            'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
            'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must',
            'shall', 'video', 'youtube', 'channel', 'like', 'subscribe', 'comment', 'watch'
        }
        
        self.question_patterns = [
            r'\bhow to\b',
            r'\bwhat about\b',
            r'\bcan you explain\b',
            r'\bnext video on\b',
            r'\bplease make\b',
            r'\bdo a video\b',
            r'\btutorial on\b',
            r'\bshow us\b',
            r'\bteach us\b',
            r'\bwould love to see\b'
        ]
    
    async def analyze_video_comments(self, video_data: Dict, comments: List[Dict]) -> VideoAnalysis:
        """Perform comprehensive analysis on video comments"""
        try:
            if not comments:
                return self._create_empty_analysis(video_data)
            
            # Analyze sentiment for each comment
            analyzed_comments = []
            sentiments = []
            
            for comment_data in comments:
                sentiment = self._analyze_sentiment(comment_data["text"])
                sentiments.append(sentiment)
                
                analyzed_comment = Comment(
                    text=comment_data["text"],
                    sentiment=sentiment,
                    author=comment_data["author"],
                    likeCount=comment_data["likeCount"]
                )
                analyzed_comments.append(analyzed_comment)
            
            # Calculate sentiment summary
            sentiment_summary = self._calculate_sentiment_summary(sentiments)
            
            # Extract keywords
            top_keywords = self._extract_keywords([c["text"] for c in comments])
            
            # Identify pros and cons
            pros, cons = self._identify_pros_cons(comments, sentiments)
            
            # Generate next topic ideas
            next_topics = self._extract_next_topic_ideas([c["text"] for c in comments])
            
            return VideoAnalysis(
                videoId=video_data["videoId"],
                title=video_data["title"],
                channelName=video_data["channelName"],
                thumbnailUrl=video_data["thumbnailUrl"],
                publishedAt=video_data["publishedAt"],
                viewCount=video_data["viewCount"],
                commentCount=len(comments),
                sentimentSummary=sentiment_summary,
                topKeywords=top_keywords,
                pros=pros,
                cons=cons,
                nextTopicIdeas=next_topics,
                comments=analyzed_comments
            )
            
        except Exception as e:
            logger.error(f"Error analyzing video comments: {str(e)}")
            return self._create_empty_analysis(video_data)
    
    async def analyze_videos_batch(
        self, 
        videos: List[Dict], 
        youtube_service, 
        api_key: str,
        progress_callback=None
    ) -> List[VideoAnalysis]:
        """Process videos sequentially with batch comment fetching and analysis"""
        results = []
        total_videos = len(videos)
        
        logger.info(f"Starting batch analysis of {total_videos} videos")
        
        for index, video in enumerate(videos, 1):
            try:
                logger.info(f"Processing video {index}/{total_videos}: {video['title']}")
                
                # Update progress if callback provided
                if progress_callback:
                    status = BatchProcessingStatus(
                        current_video=index,
                        total_videos=total_videos,
                        video_id=video["videoId"],
                        video_title=video["title"],
                        status="fetching_comments"
                    )
                    await progress_callback(status)
                
                # Fetch exactly 100 comments with pagination
                comments = await youtube_service.get_video_comments(
                    video_id=video["videoId"],
                    api_key=api_key,
                    max_results=100
                )
                
                logger.info(f"Fetched {len(comments)} comments for video {video['videoId']}")
                
                # Update progress
                if progress_callback:
                    status.status = "analyzing_comments"
                    status.comments_fetched = len(comments)
                    await progress_callback(status)
                
                # Perform comprehensive analysis
                analysis_result = await self.analyze_video_comments(
                    video_data=video,
                    comments=comments
                )
                
                # Add batch-specific metrics
                analysis_result = self._enhance_with_batch_metrics(analysis_result, comments)
                
                results.append(analysis_result)
                
                # Update progress
                if progress_callback:
                    status.status = "completed"
                    await progress_callback(status)
                
                logger.info(f"Completed analysis for video {index}/{total_videos}: {video['title']}")
                
                # Add delay between videos to respect rate limits
                if index < total_videos:
                    await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing video {video.get('videoId', 'unknown')}: {str(e)}")
                
                # Create error analysis result
                error_result = self._create_error_analysis(video, str(e))
                results.append(error_result)
                
                # Update progress with error
                if progress_callback:
                    status = BatchProcessingStatus(
                        current_video=index,
                        total_videos=total_videos,
                        video_id=video.get("videoId", "unknown"),
                        video_title=video.get("title", "Unknown"),
                        status="error",
                        error_message=str(e)
                    )
                    await progress_callback(status)
                
                continue
        
        logger.info(f"Batch analysis completed. Processed {len(results)} videos")
        return results
    
    def _enhance_with_batch_metrics(self, analysis: VideoAnalysis, comments: List[Dict]) -> VideoAnalysis:
        """Enhance analysis with additional batch processing metrics"""
        if not comments:
            return analysis
        
        # Calculate engagement metrics
        total_likes = sum(comment.get("likeCount", 0) for comment in comments)
        avg_likes = total_likes / len(comments) if comments else 0
        
        # Find top engaged comments (by likes)
        sorted_comments = sorted(comments, key=lambda x: x.get("likeCount", 0), reverse=True)
        top_engaged = sorted_comments[:5]
        
        # Calculate reply engagement
        total_replies = sum(comment.get("replyCount", 0) for comment in comments)
        avg_replies = total_replies / len(comments) if comments else 0
        
        # Add these metrics to the analysis (we'll extend the model if needed)
        # For now, we'll add them as additional keywords
        engagement_keywords = []
        if avg_likes > 10:
            engagement_keywords.append("high engagement")
        if avg_replies > 2:
            engagement_keywords.append("active discussion")
        if len([c for c in comments if c.get("likeCount", 0) > 50]) > 5:
            engagement_keywords.append("viral comments")
        
        # Merge with existing keywords
        enhanced_keywords = list(set(analysis.topKeywords + engagement_keywords))
        analysis.topKeywords = enhanced_keywords[:10]  # Keep top 10
        
        return analysis
    
    def _create_error_analysis(self, video_data: Dict, error_message: str) -> VideoAnalysis:
        """Create an error analysis result for failed video processing"""
        return VideoAnalysis(
            videoId=video_data.get("videoId", "unknown"),
            title=video_data.get("title", "Unknown Video"),
            channelName=video_data.get("channelName", "Unknown Channel"),
            thumbnailUrl=video_data.get("thumbnailUrl", ""),
            publishedAt=video_data.get("publishedAt", ""),
            viewCount=video_data.get("viewCount", 0),
            commentCount=0,
            sentimentSummary=SentimentSummary(positive=0.0, neutral=1.0, negative=0.0),
            topKeywords=[f"error: {error_message[:50]}"],
            pros=[],
            cons=[],
            nextTopicIdeas=[],
            comments=[]
        )
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of a single comment"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return "positive"
            elif polarity < -0.1:
                return "negative"
            else:
                return "neutral"
        except:
            return "neutral"
    
    def _calculate_sentiment_summary(self, sentiments: List[str]) -> SentimentSummary:
        """Calculate overall sentiment distribution"""
        if not sentiments:
            return SentimentSummary(positive=0.0, neutral=1.0, negative=0.0)
        
        sentiment_counts = Counter(sentiments)
        total = len(sentiments)
        
        return SentimentSummary(
            positive=round(sentiment_counts.get("positive", 0) / total, 3),
            neutral=round(sentiment_counts.get("neutral", 0) / total, 3),
            negative=round(sentiment_counts.get("negative", 0) / total, 3)
        )
    
    def _extract_keywords(self, comment_texts: List[str]) -> List[str]:
        """Extract top keywords using TF-IDF"""
        try:
            if not comment_texts:
                return []
            
            # Clean and preprocess texts
            cleaned_texts = []
            for text in comment_texts:
                # Remove URLs, mentions, and special characters
                cleaned = re.sub(r'http\S+|@\w+|[^\w\s]', ' ', text.lower())
                # Remove extra whitespace
                cleaned = ' '.join(cleaned.split())
                if cleaned:
                    cleaned_texts.append(cleaned)
            
            if not cleaned_texts:
                return []
            
            # Use TF-IDF to extract keywords
            vectorizer = TfidfVectorizer(
                max_features=50,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            
            tfidf_matrix = vectorizer.fit_transform(cleaned_texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores
            mean_scores = tfidf_matrix.mean(axis=0).A1
            keyword_scores = list(zip(feature_names, mean_scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Filter out stop words and return top keywords
            keywords = []
            for keyword, score in keyword_scores:
                if keyword not in self.stop_words and len(keyword) > 2:
                    keywords.append(keyword)
                if len(keywords) >= 10:
                    break
            
            return keywords[:10]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def _identify_pros_cons(self, comments: List[Dict], sentiments: List[str]) -> Tuple[List[str], List[str]]:
        """Identify pros and cons from positive and negative comments"""
        try:
            positive_comments = []
            negative_comments = []
            
            for comment, sentiment in zip(comments, sentiments):
                if sentiment == "positive":
                    positive_comments.append(comment["text"])
                elif sentiment == "negative":
                    negative_comments.append(comment["text"])
            
            # Extract pros from positive comments
            pros = self._extract_common_themes(positive_comments, is_positive=True)
            
            # Extract cons from negative comments
            cons = self._extract_common_themes(negative_comments, is_positive=False)
            
            return pros[:5], cons[:5]
            
        except Exception as e:
            logger.error(f"Error identifying pros/cons: {str(e)}")
            return [], []
    
    def _extract_common_themes(self, comments: List[str], is_positive: bool) -> List[str]:
        """Extract common themes from comments"""
        if not comments:
            return []
        
        # Positive keywords for pros
        positive_keywords = [
            'great', 'amazing', 'excellent', 'fantastic', 'awesome', 'perfect', 'love',
            'helpful', 'useful', 'clear', 'easy', 'understand', 'good', 'best',
            'informative', 'detailed', 'comprehensive', 'thorough'
        ]
        
        # Negative keywords for cons
        negative_keywords = [
            'bad', 'terrible', 'awful', 'hate', 'confusing', 'unclear', 'difficult',
            'hard', 'boring', 'slow', 'fast', 'short', 'long', 'missing', 'wrong',
            'error', 'mistake', 'problem', 'issue'
        ]
        
        keywords = positive_keywords if is_positive else negative_keywords
        themes = []
        
        for comment in comments[:20]:  # Analyze top 20 comments
            comment_lower = comment.lower()
            for keyword in keywords:
                if keyword in comment_lower:
                    # Extract context around the keyword
                    context = self._extract_context(comment, keyword)
                    if context and context not in themes:
                        themes.append(context)
                        if len(themes) >= 5:
                            break
            if len(themes) >= 5:
                break
        
        return themes
    
    def _extract_context(self, comment: str, keyword: str) -> str:
        """Extract meaningful context around a keyword"""
        try:
            # Find sentences containing the keyword
            sentences = re.split(r'[.!?]+', comment)
            for sentence in sentences:
                if keyword.lower() in sentence.lower():
                    # Clean and return the sentence
                    cleaned = re.sub(r'[^\w\s]', ' ', sentence).strip()
                    cleaned = ' '.join(cleaned.split())
                    if len(cleaned) > 10 and len(cleaned) < 100:
                        return cleaned
            return ""
        except:
            return ""
    
    def _extract_next_topic_ideas(self, comment_texts: List[str]) -> List[str]:
        """Extract potential next topic ideas from comments"""
        try:
            topic_ideas = []
            
            for comment in comment_texts:
                comment_lower = comment.lower()
                
                # Check for question patterns
                for pattern in self.question_patterns:
                    matches = re.finditer(pattern, comment_lower)
                    for match in matches:
                        # Extract the topic after the pattern
                        start_pos = match.end()
                        remaining_text = comment[start_pos:start_pos + 100]
                        
                        # Clean and extract the topic
                        topic = re.sub(r'[^\w\s]', ' ', remaining_text).strip()
                        topic = ' '.join(topic.split())
                        
                        if len(topic) > 5 and len(topic) < 50:
                            topic_ideas.append(topic)
                            if len(topic_ideas) >= 4:
                                break
                
                if len(topic_ideas) >= 4:
                    break
            
            # Remove duplicates while preserving order
            unique_topics = []
            for topic in topic_ideas:
                if topic not in unique_topics:
                    unique_topics.append(topic)
            
            return unique_topics[:4]
            
        except Exception as e:
            logger.error(f"Error extracting next topic ideas: {str(e)}")
            return []
    
    def _create_empty_analysis(self, video_data: Dict) -> VideoAnalysis:
        """Create an empty analysis for videos with no comments"""
        return VideoAnalysis(
            videoId=video_data["videoId"],
            title=video_data["title"],
            channelName=video_data["channelName"],
            thumbnailUrl=video_data["thumbnailUrl"],
            publishedAt=video_data["publishedAt"],
            viewCount=video_data["viewCount"],
            commentCount=0,
            sentimentSummary=SentimentSummary(positive=0.0, neutral=1.0, negative=0.0),
            topKeywords=[],
            pros=[],
            cons=[],
            nextTopicIdeas=[],
            comments=[]
        )