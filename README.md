# 🎨 AI-Powered System Design Copilot

**"GitHub Copilot for System Architecture"**

An intelligent system design tool that provides real-time AI suggestions for drawing system architecture diagrams. Built with FastAPI, Next.js, and Excalidraw, following strict architectural guidelines for reliable and safe AI integration.

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org)

## 🚀 Features

- **🤖 Real-time AI Suggestions**: Get intelligent architectural recommendations as you draw
- **🎯 Pattern Recognition**: Automatically detects common system design patterns
- **⚡ Fast Performance**: Sub-2s response times with debounced API calls
- **🛡️ Type Safety**: Full TypeScript and Pydantic validation
- **📊 Structured Logging**: Complete request/response audit trail
- **🔧 Multiple LLM Support**: Configurable OpenAI, Anthropic, and Groq integration
- **📚 Comprehensive Documentation**: Auto-generated OpenAPI/Swagger docs

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP/WebSocket    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │ ─────────────────► │   FastAPI        │◄──►│  LangChain      │
│   + Excalidraw   │ ◄───────────────── │   + Pydantic     │    │  + LLM Providers│
└─────────────────┘   Real-time         └──────────────────┘    └─────────────────┘
        │             Suggestions                │                        │
        ▼                                       ▼                        ▼
┌─────────────────┐              ┌──────────────────┐    ┌─────────────────┐
│  Canvas Drawing │              │  Pattern Analysis│    │  Architectural  │
│  + Change Det.  │              │  + Validation    │    │  Knowledge Base │
└─────────────────┘              └──────────────────┘    └─────────────────┘
```

## 📋 Quick Start

### Prerequisites

- **Python 3.11+** with `uv` package manager
- **Node.js 18+** with npm/pnpm
- **Git** for version control

### 1. Clone Repository

```bash
git clone https://github.com/your-username/ai-design-copilot
cd ai-design-copilot
```

### 2. Backend Setup (FastAPI)

```bash
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt -r requirements-dev.txt

# Configure environment variables
cp .env.template .env
# Edit .env and add your API keys

# Run backend server
uvicorn main:app --reload
```

Backend will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

### 3. Frontend Setup (Next.js)

```bash
cd frontend

# Install dependencies  
npm install
# or: pnpm install

# Run development server
npm run dev
```

Frontend will be available at:
- **Main App**: http://localhost:3000
- **API Test**: http://localhost:3000/test-api.html

### 4. Test the Integration

1. Open http://localhost:3000 in your browser
2. Draw rectangles and label them (e.g., "client app", "database")
3. Watch for real-time AI suggestions
4. Check the backend logs for request/response details

## 🎯 How It Works

### 1. Drawing Recognition
- User draws components in Excalidraw canvas
- System detects text labels and component types
- Canvas changes trigger debounced API calls

### 2. AI Analysis
- Backend analyzes canvas elements using pattern matching
- Identifies architectural patterns and missing components
- Generates suggestions following strict ontology rules

### 3. Real-time Feedback
- AI suggestions appear as overlays on the canvas
- Users can accept, reject, or modify suggestions
- System learns from user interactions

## 📚 API Documentation

### Core Endpoints

#### `POST /api/v1/suggest`
Generate AI architectural suggestions based on canvas state.

**Request:**
```json
{
  "canvas_elements": [
    {
      "id": "client-1",
      "type": "rectangle",
      "text": "Mobile App",
      "x": 100, "y": 100,
      "width": 120, "height": 60
    }
  ],
  "context": {
    "user_id": "demo-user",
    "session_id": "session-123"
  }
}
```

**Response:**
```json
{
  "suggestion": {
    "nodes": [
      {
        "type": "api-gateway",
        "label": "API Gateway",
        "id": "gateway-1"
      }
    ],
    "edges": [
      {
        "from": "client-1",
        "to": "gateway-1", 
        "type": "requests"
      }
    ]
  },
  "reasoning": "Added API Gateway to manage and secure API requests from the mobile app.",
  "reference": "https://microservices.io/patterns/apigateway.html"
}
```

#### `GET /health`
Main API health check.

#### `GET /api/v1/health`
Suggestion service health check with pattern count.

### Interactive Documentation

Visit http://localhost:8000/docs for complete interactive API documentation with:
- **Try It Out**: Test endpoints directly in the browser
- **Schema Details**: Complete request/response models
- **Example Requests**: Real-world usage examples
- **Error Handling**: All possible error responses

## 🏗️ System Design Ontology

### Node Types
- `client` - User-facing applications
- `webserver` - HTTP servers and APIs
- `api-gateway` - API management layer
- `cache` - Caching systems (Redis, Memcached)
- `database` - Data storage systems
- `worker` - Background processing services
- `queue` - Message queuing systems
- `storage` - File/blob storage systems

### Edge Types
- `requests` - HTTP/API requests
- `reads-from` - Data read operations
- `writes-to` - Data write operations
- `sends-message` - Message/event publishing
- `connects-to` - Generic connections
- `depends-on` - Service dependencies

## 🔧 Development

### Backend Development

```bash
cd backend

# Run tests
pytest tests/ -v

# Code formatting
black .
flake8 .
isort .

# Start with auto-reload
uvicorn main:app --reload --log-level debug
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build
```

### Project Structure

```
ai-design-copilot/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI application
│   ├── models/schema.py       # Pydantic models
│   ├── routers/suggest.py     # API endpoints
│   ├── services/              # Business logic
│   ├── tests/                 # Test suite
│   └── logs/llm/             # Request/response logs
├── frontend/                   # Next.js frontend  
│   ├── src/app/              # Next.js app router
│   ├── src/components/       # React components
│   ├── src/lib/              # API clients & utilities
│   └── src/types/            # TypeScript definitions
└── docs/                      # Additional documentation
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

Test coverage includes:
- **Unit tests**: Pydantic models, services
- **Integration tests**: API endpoints, request/response flow
- **Validation tests**: Input validation, error handling

### Frontend Tests (Future)

```bash
cd frontend
npm test
```

## 🚀 Deployment

### Backend (FastAPI)

**Option 1: Docker**
```bash
cd backend
docker build -t ai-design-copilot-backend .
docker run -p 8000:8000 ai-design-copilot-backend
```

**Option 2: Railway/Render**
- Connect GitHub repository
- Set environment variables
- Deploy automatically on push

### Frontend (Next.js)

**Vercel (Recommended)**
```bash
cd frontend
npm run build
vercel deploy
```

**Other Options**
- Netlify
- Railway
- DigitalOcean App Platform

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow **CLAUDE.md** rules for AI integration
- Maintain **type safety** (TypeScript + Pydantic)
- Add **tests** for new features
- Update **documentation** for API changes
- Use **structured logging** for debugging

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Documentation**: Check `/docs` endpoint for API details
- **Issues**: Create GitHub issues for bugs/features
- **Discussions**: Use GitHub Discussions for questions

## 🎯 Roadmap

- [ ] **WebSocket Support** - Real-time bidirectional communication
- [ ] **LLM Integration** - Replace hardcoded patterns with real LLMs
- [ ] **Vector Database** - Add ChromaDB/Supabase for pattern storage
- [ ] **Authentication** - User accounts and API keys
- [ ] **Collaboration** - Multi-user drawing sessions
- [ ] **Export/Import** - Save and share system designs

---

**Built with ❤️ for better system design**