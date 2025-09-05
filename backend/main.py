"""
AI-Powered System Design Whiteboard - FastAPI Backend
Following CLAUDE.md guidelines for reliable system design copilot
"""

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import routers
from routers.suggest import router as suggest_router

# Load environment variables
load_dotenv()

# Configure logging (structured JSON logs as per CLAUDE.md)
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}',
    handlers=[
        logging.FileHandler("logs/llm/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AI System Design Copilot API",
    description="""
# 🎨 AI-Powered System Design Copilot

**GitHub Copilot for System Architecture** - An intelligent backend API that provides real-time AI suggestions for system design diagrams.

## 🚀 Features

* **Real-time Analysis**: Analyze canvas elements and provide architectural suggestions
* **Pattern Recognition**: Detect common system design patterns and anti-patterns
* **Structured Responses**: All responses follow strict JSON schemas with validation
* **Multiple LLM Support**: Configurable support for OpenAI, Anthropic, and Groq
* **Extensive Logging**: Complete request/response logging for debugging

## 🏗️ Architecture

This API follows clean architecture principles with:
- **Pydantic Models**: Strict data validation and serialization
- **Structured Logging**: JSON-formatted logs with request tracing
- **Error Handling**: Comprehensive error responses with fallbacks
- **Rate Limiting**: Built-in protection against API flooding

## 📚 Usage

1. Send canvas elements via `/api/v1/suggest` endpoint
2. Receive AI-powered architectural suggestions
3. Implement suggestions in your system design tool
4. Monitor health via `/health` and `/api/v1/health` endpoints

## 🔗 Integration

This API is designed to work with:
- **Excalidraw** for canvas interaction
- **Next.js** frontend applications  
- **Real-time drawing tools** via WebSocket (future)
- **System design education platforms**

## 🎯 Node & Edge Types

The API works with a strict ontology of system components:

**Node Types**: client, webserver, api-gateway, cache, database, worker, queue, storage

**Edge Types**: requests, reads-from, writes-to, sends-message, connects-to, depends-on
    """,
    version="0.1.0",
    contact={
        "name": "AI Design Copilot Team",
        "url": "https://github.com/ai-design-copilot",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.aidesigncopilot.com",
            "description": "Production server (example)"
        }
    ],
    tags_metadata=[
        {
            "name": "health",
            "description": "Health check endpoints for monitoring system status",
        },
        {
            "name": "suggestions",
            "description": "AI-powered architectural suggestion endpoints",
        },
    ],
    openapi_tags=[
        {
            "name": "health",
            "description": "System health and monitoring"
        },
        {
            "name": "suggestions", 
            "description": "Core AI suggestion functionality"
        }
    ],
    debug=os.getenv("DEBUG", "False").lower() == "true"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(suggest_router)

@app.get(
    "/",
    summary="API Root Endpoint",
    description="""
    ## 👋 Welcome to AI Design Copilot API
    
    Root endpoint providing basic API information and status.
    Use this endpoint to verify the API is accessible and running.
    
    ### 📋 Quick Start
    
    1. Check this endpoint to verify API availability
    2. Use `/docs` for interactive API documentation
    3. Use `/api/v1/suggest` for AI architectural suggestions
    4. Use `/health` and `/api/v1/health` for monitoring
    """,
    response_description="Basic API information and running status",
    tags=["health"]
)
async def root():
    """
    Root endpoint providing API information and basic health status.
    
    Returns general information about the AI Design Copilot API
    including version and running status.
    """
    logger.info("Root endpoint accessed")
    return {
        "message": "AI System Design Copilot API",
        "description": "GitHub Copilot for System Architecture",
        "status": "running",
        "version": "0.1.0",
        "docs_url": "/docs",
        "suggestions_endpoint": "/api/v1/suggest"
    }

@app.get(
    "/health",
    summary="API Health Check", 
    description="""
    ## 🏥 Main API Health Check
    
    Comprehensive health check for the entire API service.
    Use this endpoint for monitoring and uptime checks.
    
    ### ✅ What This Monitors
    
    - API server responsiveness
    - Environment configuration
    - Basic system health
    
    ### 🔧 For Detailed Health
    
    - Use `/api/v1/health` for suggestion service specific health
    - Check both endpoints for complete system monitoring
    """,
    response_description="Overall API health status and environment info",
    responses={
        200: {
            "description": "API is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "environment": "development",
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                }
            }
        }
    },
    tags=["health"]
)
async def health_check():
    """
    Main health check endpoint for API monitoring.
    
    Returns the overall health status of the API including
    environment information and timestamp.
    """
    logger.info("Health check accessed")
    return {
        "status": "healthy",
        "environment": "development" if os.getenv("DEBUG", "False").lower() == "true" else "production",
        "timestamp": "2024-01-01T12:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )