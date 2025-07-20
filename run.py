#!/usr/bin/env python3
"""
YouTube Comment Analyzer API Runner

This script starts the FastAPI server for the YouTube Comment Analyzer.
Make sure to set your YouTube API key in the .env file before running.
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("🚀 Starting YouTube Comment Analyzer API...")
    print(f"📡 Server will run on http://{settings.API_HOST}:{settings.API_PORT}")
    print("📚 API documentation available at http://localhost:8000/docs")
    print("⚠️  Make sure to set your YOUTUBE_API_KEY in the .env file")
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )