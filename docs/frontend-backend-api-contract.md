# Frontend-Backend API Contract

This document specifies what the frontend expects from the backend APIs.

## Base Configuration

- **Backend URL**: `http://localhost:8000` (from `NEXT_PUBLIC_API_URL`)
- **Request Timeout**: 10 seconds
- **Content-Type**: `application/json`

## API Endpoints

### 1. Health Check - Basic API
**Endpoint**: `GET /health`

**Expected Response**:
```json
{
  "status": "healthy",
  "environment": "development",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. Health Check - Suggestion Service
**Endpoint**: `GET /api/v1/health`

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "suggestion_router",
  "patterns_loaded": 5
}
```

### 3. Get Providers
**Endpoint**: `GET /api/v1/providers`

**Expected Response**:
```json
{
  "available_providers": ["groq", "openai", "anthropic"],
  "current_provider": "groq",
  "provider_status": {
    "groq": true,
    "openai": false,
    "anthropic": false
  }
}
```

### 4. Switch Provider
**Endpoint**: `POST /api/v1/providers/switch`

**Request Body**:
```json
{
  "provider": "groq"
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Switched to groq",
  "current_provider": "groq",
  "previous_provider": "openai"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Provider 'invalid' not available"
}
```

### 5. Get AI Suggestions
**Endpoint**: `POST /api/v1/suggest`

**Request Body**:
```json
{
  "session_id": "session-1234567890-abcdef123",
  "canvas_elements": [
    {
      "id": "element-1",
      "type": "rectangle",
      "text": "API Gateway",
      "x": 100,
      "y": 100,
      "width": 100,
      "height": 50
    }
  ],
  "recent_changes": [
    {
      "action": "add",
      "element_id": "element-1",
      "element": {
        "id": "element-1",
        "type": "rectangle",
        "text": "API Gateway",
        "x": 100,
        "y": 100
      },
      "timestamp": "2024-01-01T12:00:00.000Z"
    }
  ],
  "context": {
    "user_id": "demo-user",
    "timestamp": "2024-01-01T12:00:00.000Z",
    "has_memory": true
  }
}
```

**Expected Response**:
```json
{
  "suggestion": {
    "nodes": [
      {
        "type": "cache",
        "label": "Redis Cache",
        "id": "redis-cache-1"
      }
    ],
    "edges": [
      {
        "from": "web-server-1",
        "to": "redis-cache-1",
        "type": "reads-from"
      }
    ]
  },
  "reasoning": "Added Redis cache to improve database read performance and reduce query latency for frequently accessed data.",
  "reference": "https://redis.io/docs/about/"
}
```

**No Suggestion Response**:
```json
{
  "suggestion": null,
  "reasoning": "Current architecture appears well-designed with appropriate components and connections.",
  "reference": null
}
```

## TypeScript Types

The frontend defines these TypeScript interfaces:

### Node Types
```typescript
type NodeType = 
  | "client" 
  | "webserver" 
  | "api-gateway" 
  | "cache" 
  | "database" 
  | "worker" 
  | "queue" 
  | "storage";
```

### Edge Types  
```typescript
type EdgeType = 
  | "requests" 
  | "reads-from" 
  | "writes-to" 
  | "sends-message" 
  | "connects-to" 
  | "depends-on";
```

### Core Interfaces
```typescript
interface Node {
  type: NodeType;
  label: string;
  id?: string;
}

interface Edge {
  from: string;  // ← IMPORTANT: Uses "from", not "from_node"
  to: string;    // ← IMPORTANT: Uses "to", not "to_node"
  type: EdgeType;
  label?: string;
}

interface Suggestion {
  nodes: Node[];
  edges: Edge[];
}

interface SuggestionResponse {
  suggestion: Suggestion | null;
  reasoning: string;
  reference: string | null;
}

interface ProvidersResponse {
  available_providers: string[];
  current_provider: string | null;
  provider_status: Record<string, boolean>;
}
```

## Error Handling

The frontend expects errors in this format:
```typescript
interface APIError {
  error: string;
  details?: string;
  request_id?: string;
}
```

Example error responses:
```json
{
  "error": "Network Error",
  "details": "Could not connect to backend server. Make sure it's running on port 8000."
}
```

```json
{
  "error": "Provider Switch Failed", 
  "details": "Provider 'invalid' not available"
}
```

## Frontend Behavior

### Rate Limiting & Debouncing
- **Debounce**: 5 seconds before making suggestion API calls
- **Rate Limit**: Maximum 1 suggestion API call per 10 seconds
- **Significant Changes**: Only calls API when meaningful changes are detected (text changes, major position/size changes)

### Provider Management
- **Default Provider**: Groq (hardcoded, no initial API call)
- **Manual Refresh**: User can manually sync provider status with backend
- **Offline Mode**: Works without backend connectivity for provider selection

### Session Management
- **Session ID**: Auto-generated and stored in localStorage
- **Format**: `session-{timestamp}-{random}`
- **Persistence**: Maintained across page reloads

### Canvas Integration
- **Health Checks**: Disabled to reduce network traffic
- **Element Format**: Converts Excalidraw elements to API format
- **Change Detection**: Tracks additions, modifications, and deletions
- **Context**: Includes user ID, timestamp, and memory status

## CORS Requirements

The backend must allow these origins:
- `http://localhost:3000` (Next.js dev server)
- `http://localhost:3001` (Alternative port)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

Required headers:
- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods: *`
- `Access-Control-Allow-Headers: *`
- `Access-Control-Allow-Credentials: true`

## Critical Requirements

1. **Edge Field Names**: Must use `from` and `to`, not `from_node` and `to_node`
2. **Provider Status**: Must return boolean values for `provider_status`
3. **Null Handling**: `suggestion` can be `null`, `reference` can be `null`
4. **Node IDs**: Should be unique and descriptive (e.g., `redis-cache-1`)
5. **Response Times**: Suggestion endpoint should respond within 30 seconds maximum