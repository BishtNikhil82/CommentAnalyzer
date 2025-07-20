# YouTube Comment Analyzer API

A comprehensive Python API that analyzes YouTube comments for content insights, sentiment analysis, and trend identification.

## Features

- **Video Search**: Search YouTube videos with advanced filtering options
- **Comment Extraction**: Retrieve up to 100 top-level comments per video
- **Sentiment Analysis**: Classify comments as positive, neutral, or negative
- **Keyword Extraction**: Identify the most relevant terms using TF-IDF
- **Pros/Cons Analysis**: Extract common praise points and criticism patterns
- **Next Topic Suggestions**: Identify potential follow-up content ideas
- **Rate Limiting**: Built-in protection against API quota exhaustion

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Configuration

Edit the `.env` file and add your YouTube Data API v3 key:

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
```

To get a YouTube API key:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API key)
5. Copy the API key to your `.env` file

### 3. Run the API

```bash
# Start the development server
python run.py

# Or use uvicorn directly
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

### Endpoint: `GET /analyze-youtube`

Analyzes YouTube comments for content insights and sentiment analysis.

#### Required Parameters

- `query` (string): YouTube search keyword/phrase
- `video_count` (integer): Number of videos to analyze (1-50)
- `api_key` (string): YouTube Data API v3 access key

#### Optional Parameters

- `filters` (JSON string): Search filters including:
  - `upload_date`: "hour", "today", "week", "month", "year"
  - `duration`: "short" (<4min), "medium" (4-20min), "long" (>20min)
  - `sort_by`: "relevance", "date", "viewCount", "rating"
  - `language`: ISO language code (e.g., "en", "es")

#### Example Request

```bash
curl "http://localhost:8000/analyze-youtube?query=python%20tutorial&video_count=2&api_key=YOUR_API_KEY&filters=%7B%22upload_date%22:%22week%22,%22sort_by%22:%22viewCount%22%7D"
```

#### Example Response

```json
[
  {
    "videoId": "dQw4w9WgXcQ",
    "title": "Python Tutorial for Beginners",
    "channelName": "Tech Channel",
    "thumbnailUrl": "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
    "publishedAt": "2023-12-01T10:00:00Z",
    "viewCount": 50000,
    "commentCount": 95,
    "sentimentSummary": {
      "positive": 0.65,
      "neutral": 0.25,
      "negative": 0.10
    },
    "topKeywords": ["python", "tutorial", "beginner", "programming", "code"],
    "pros": ["clear explanations", "good examples", "easy to follow"],
    "cons": ["too fast", "missing advanced topics"],
    "nextTopicIdeas": ["object oriented programming", "web development with flask"],
    "comments": [
      {
        "text": "Great tutorial! Very clear explanations.",
        "sentiment": "positive",
        "author": "CodeLearner123",
        "likeCount": 15
      }
    ]
  }
]
```

## Interactive Documentation

Visit `http://localhost:8000/docs` for the interactive Swagger UI documentation where you can test the API directly.

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

## Error Handling

The API handles various error scenarios:

- **403**: Invalid or expired YouTube API key
- **429**: YouTube API quota exceeded or rate limit hit
- **404**: No videos found for the given query
- **400**: Invalid request parameters or filters
- **500**: Internal server errors

## Rate Limiting

The API includes built-in rate limiting (60 requests per minute by default) to prevent API quota exhaustion. This can be configured in the `.env` file:

```env
MAX_REQUESTS_PER_MINUTE=60
```

## Architecture

The project follows a clean architecture pattern:

```
app/
├── main.py              # FastAPI application and routes
├── config.py            # Configuration settings
├── models.py            # Pydantic models
├── services/
│   ├── youtube_service.py    # YouTube API integration
│   └── analysis_service.py   # Comment analysis logic
└── utils/
    └── rate_limiter.py       # Rate limiting utility
```

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **TextBlob**: Natural language processing for sentiment analysis
- **scikit-learn**: Machine learning library for TF-IDF keyword extraction
- **httpx**: Async HTTP client for YouTube API calls
- **pydantic**: Data validation and settings management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.