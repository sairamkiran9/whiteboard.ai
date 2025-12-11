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
* **Canvas-Aware Intelligence**: Full Excalidraw parser with spatial context understanding
* **Ghost Elements**: Ready-to-render suggestion previews on canvas
* **Extensive Logging**: Complete request/response logging for debugging

## 🏗️ Architecture

This API follows clean architecture principles with:
- **Pydantic Models**: Strict data validation and serialization (OpenAPI 3.0 compatible)
- **Canvas-Aware HLD Agent**: Multi-agent LLM system with spatial awareness
- **Excalidraw Parser**: Extract components, connections, and detect incomplete flows
- **Structured Logging**: JSON-formatted logs with request tracing
- **Error Handling**: Comprehensive error responses with safe fallbacks
- **Type Safety**: Full TypeScript-compatible schemas

## 📚 Usage

1. Send canvas elements via `/api/v1/suggest` endpoint
2. Receive AI-powered architectural suggestions with ghost elements
3. Render suggestions on Excalidraw canvas
4. Monitor health via `/health` and `/api/v1/health` endpoints
5. Access OpenAPI docs at `/docs` or `/redoc`

## 🔗 Integration

This API is designed to work with:
- **Excalidraw** for canvas interaction
- **Next.js** frontend applications
- **React** with TypeScript
- **System design education platforms**

## 🎯 Node & Edge Types

The API works with a strict ontology of system components:

**Node Types**: `client`, `webserver`, `api-gateway`, `cache`, `database`, `worker`, `queue`, `storage`

**Edge Types**: `requests`, `reads-from`, `writes-to`, `sends-message`, `connects-to`, `depends-on`

## 📖 OpenAPI 3.0 Specification

This API fully conforms to OpenAPI 3.0.0 specification with:
- Complete request/response schemas
- Multiple example responses for each endpoint
- Detailed error codes and descriptions
- Code samples in JavaScript, Python, and cURL
- Type-safe Pydantic models

Access the OpenAPI spec at `/openapi.json`
    """,
    version="0.1.0",
    contact={
        "name": "AI Design Copilot Team",
        "url": "https://github.com/ai-design-copilot",
        "email": "support@aidesigncopilot.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server",
            "variables": {}
        },
        {
            "url": "https://api.aidesigncopilot.com",
            "description": "Production server (example)"
        }
    ],
    openapi_tags=[
        {
            "name": "health",
            "description": "System health and monitoring endpoints",
            "externalDocs": {
                "description": "Health check best practices",
                "url": "https://microservices.io/patterns/observability/health-check-api.html"
            }
        },
        {
            "name": "suggestions",
            "description": "Core AI suggestion functionality using Canvas-Aware HLD Agent",
            "externalDocs": {
                "description": "API documentation",
                "url": "https://github.com/ai-design-copilot/docs"
            }
        },
        {
            "name": "providers",
            "description": "LLM provider configuration and switching (Groq, OpenAI, Anthropic)"
        }
    ],
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.0.0",
    terms_of_service="https://aidesigncopilot.com/terms",
    debug=os.getenv("DEBUG", "False").lower() == "true",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 3,
        "defaultModelExpandDepth": 3,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "syntaxHighlight.theme": "monokai"
    }
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default port
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
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
    "/openapi-schema",
    summary="Get Enhanced OpenAPI Schema",
    description="""
    ## 📖 OpenAPI 3.0 Schema Endpoint

    Returns the complete OpenAPI 3.0 JSON schema for this API.

    ### 🎯 Use Cases

    - Generate API clients (openapi-generator, swagger-codegen)
    - Create TypeScript types from schema
    - Import into Postman/Insomnia
    - Validate API contracts

    ### 📋 Schema Includes

    - All endpoints with detailed descriptions
    - Request/response models with examples
    - Authentication schemes (if configured)
    - Error response formats
    - Code samples for JavaScript, Python, cURL

    This is the same schema available at `/openapi.json` but with
    additional metadata and formatting.
    """,
    response_description="Complete OpenAPI 3.0 specification",
    tags=["health"],
    operation_id="getOpenAPISchema"
)
async def get_openapi_schema():
    """
    Return the OpenAPI schema for this API.

    Useful for API client generation and documentation.
    """
    from fastapi.openapi.utils import get_openapi

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add custom extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://aidesigncopilot.com/logo.png"
    }

    app.openapi_schema = openapi_schema
    return openapi_schema


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

    ### 📊 OpenAPI 3.0

    This endpoint returns standardized health check format compatible with
    Kubernetes liveness/readiness probes.
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
                        "timestamp": "2024-01-01T12:00:00Z",
                        "version": "0.1.0"
                    }
                }
            }
        },
        503: {
            "description": "Service Unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "error": "Service degraded"
                    }
                }
            }
        }
    },
    tags=["health"],
    operation_id="healthCheck"
)
async def health_check():
    """
    Main health check endpoint for API monitoring.

    Returns the overall health status of the API including
    environment information and timestamp.
    """
    from datetime import datetime

    logger.info("Health check accessed")
    return {
        "status": "healthy",
        "environment": "development" if os.getenv("DEBUG", "False").lower() == "true" else "production",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )