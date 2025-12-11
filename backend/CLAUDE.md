# **CLAUDE.md — Backend-Specific LLM Rules for HLD Agent**

This document defines strict guidelines for the **Python backend** of the Excalidraw HLD Agent system.

---

## **I. Backend Architecture Principles**

### **1. Modular Design**
- **Separation of Concerns**: Each module has a single, well-defined responsibility
  - `parsers/` - Excalidraw JSON parsing only
  - `analyzers/` - Graph analysis and pattern detection
  - `agents/` - LLM-based suggestion generation
  - `services/` - Business logic and orchestration
  - `api/` - FastAPI routes and request handling

- **No Cross-Contamination**: Parsers don't call agents, agents don't handle HTTP

### **2. Data Flow is Unidirectional**
```
Excalidraw JSON → Parser → ArchitectureGraph → Analyzer → Agents → Suggestions → API Response
```
- Each stage produces **immutable** outputs
- No backwards dependencies (agents can't modify the graph)

### **3. Fail-Safe Defaults**
- If parser fails → Return empty graph, log error
- If agent fails → Return empty suggestions, don't crash
- If LLM times out → Use cached/default suggestions
- **Never return partial/corrupt data** to frontend

---

## **II. Python Code Quality Standards**

### **1. Type Hints (Mandatory)**
```python
# ✅ GOOD
def parse_canvas(data: Dict[str, Any]) -> ArchitectureGraph:
    components: List[ComponentNode] = []
    # ...

# ❌ BAD
def parse_canvas(data):  # No type hints
    components = []
```

### **2. Pydantic for All Data Models**
```python
# ✅ GOOD
class ComponentNode(BaseModel):
    id: str = Field(..., description="Unique ID")
    name: str
    type: str

# ❌ BAD
class ComponentNode:
    def __init__(self, id, name, type):  # Not validated
        self.id = id
```

### **3. Error Handling**
```python
# ✅ GOOD
try:
    graph = parser.parse(canvas_data)
except ExcalidrawParseError as e:
    logger.error(f"Parse failed: {e}", exc_info=True)
    return ArchitectureGraph()  # Safe default

# ❌ BAD
graph = parser.parse(canvas_data)  # No error handling
```

### **4. Logging Standards**
```python
import logging
import json

logger = logging.getLogger(__name__)

# ✅ GOOD - Structured JSON logging
logger.info(
    "Canvas parsed",
    extra={
        "component_count": len(graph.components),
        "connection_count": len(graph.connections),
        "canvas_hash": canvas_hash
    }
)

# ❌ BAD - Unstructured string logging
logger.info(f"Parsed {len(graph.components)} components")  # Hard to query
```

---

## **III. Excalidraw Parser Rules**

### **1. Parse Defensively**
- Assume Excalidraw format may change
- Handle missing fields gracefully
- Validate all extracted data

```python
# ✅ GOOD
element = raw_element.get("type", "unknown")
x = float(raw_element.get("x", 0))

# ❌ BAD
element = raw_element["type"]  # KeyError if missing
x = raw_element["x"]  # May not be float
```

### **2. Component Name Extraction**
- Text with `containerId` → Component label
- Text without `containerId` → Standalone annotation (ignore for now)

```python
if text_element.get("containerId"):
    # This text labels a component
    component_id = text_element["containerId"]
    component_name = text_element["text"]
```

### **3. Connection Detection**
- Arrow with `startBinding` and `endBinding` → Complete connection
- Arrow with only `startBinding` → Incomplete (suggest target component)

```python
if arrow.get("startBinding") and arrow.get("endBinding"):
    # Complete connection
    edge = ConnectionEdge(
        from_component=arrow["startBinding"]["elementId"],
        to_component=arrow["endBinding"]["elementId"]
    )
else:
    # Incomplete arrow - suggestion opportunity
    edge = ConnectionEdge(
        from_component=arrow["startBinding"]["elementId"],
        to_component=None  # Mark as incomplete
    )
```

---

## **IV. Multi-Agent LLM Integration**

### **1. Structured Outputs Only (Instructor)**
```python
from instructor import from_groq
import groq

client = from_groq(
    groq.Groq(api_key=os.environ["GROQ_API_KEY"]),
    mode=instructor.Mode.JSON
)

# ✅ GOOD - Pydantic response model
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    response_model=ComponentSuggestion,  # Pydantic model
    messages=[...]
)

# ❌ BAD - Unstructured output
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[...]
)
raw_text = response.choices[0].message.content  # Unvalidated
```

### **2. Prompt Engineering Standards**

#### **System Prompts: Clear Role + Constraints**
```python
NEXT_COMPONENT_SYSTEM = """You are a senior distributed systems architect.

Your task: Suggest the next logical component to add to an architecture diagram.

Rules:
1. Return ONLY valid JSON matching ComponentSuggestion schema
2. Suggest exactly ONE component (not multiple)
3. Provide clear reasoning based on current architecture
4. Consider incomplete connections (arrows pointing nowhere)
5. Follow industry best practices (AWS Well-Architected, 12-factor)

Allowed component types:
- api-gateway, load-balancer, service, database, cache, queue, worker, storage, auth, monitoring
"""
```

#### **User Prompts: Structured Context**
```python
def build_user_prompt(graph: ArchitectureGraph) -> str:
    return f"""
Current Architecture:
Components: {', '.join(graph.get_component_names())}
Connections: {format_connections(graph.connections)}
Incomplete flows: {len(graph.get_incomplete_connections())}

Context:
- Total components: {len(graph.components)}
- Detected patterns: {', '.join(graph.patterns_detected) or 'None'}

Task: Suggest the next most logical component to add.
"""
```

### **3. Agent Independence**
- Each agent runs **independently** (no shared state)
- Agents don't communicate with each other directly
- Results are aggregated by `SuggestionRanker`

```python
# ✅ GOOD - Parallel execution
async def run_all_agents(graph: ArchitectureGraph) -> AgentResponse:
    results = await asyncio.gather(
        next_component_agent.suggest(graph),
        pattern_agent.complete_pattern(graph),
        critic_agent.critique(graph),
        return_exceptions=True  # Don't fail if one agent fails
    )
    return ranker.aggregate(results)

# ❌ BAD - Sequential execution
def run_all_agents(graph):
    r1 = next_component_agent.suggest(graph)
    r2 = pattern_agent.complete_pattern(graph)  # Waits for r1
    r3 = critic_agent.critique(graph)  # Waits for r2
```

### **4. LLM Error Handling**
```python
# ✅ GOOD
try:
    suggestion = await llm_client.suggest(graph)
except (GroqAPIError, TimeoutError, ValidationError) as e:
    logger.error(f"LLM call failed: {e}", exc_info=True)
    suggestion = ComponentSuggestion(
        component_name="Database",  # Fallback suggestion
        reasoning="Default suggestion due to LLM failure",
        confidence=0.3,  # Low confidence
        priority="medium"
    )

# ❌ BAD
suggestion = await llm_client.suggest(graph)  # No error handling
```

### **5. Token Usage Optimization**
- Limit graph context to **last 10 components** (don't send entire history)
- Use smaller models for simple tasks (pattern detection → `gemma2-9b-it`)
- Cache expensive LLM calls (same graph → same suggestions)

```python
def truncate_graph_for_llm(graph: ArchitectureGraph) -> ArchitectureGraph:
    """Only send recent components to LLM to save tokens"""
    return ArchitectureGraph(
        components=graph.components[-10:],  # Last 10 only
        connections=graph.connections[-15:],
        patterns_detected=graph.patterns_detected
    )
```

---

## **V. Architecture Analysis Rules**

### **1. Pattern Detection Logic**

#### **Microservices Pattern**
```python
def detect_microservices(graph: ArchitectureGraph) -> bool:
    service_count = len([c for c in graph.components if c.type == "service"])
    has_gateway = any(c.type == "api-gateway" for c in graph.components)
    return service_count >= 2 and has_gateway
```

#### **Event-Driven Pattern**
```python
def detect_event_driven(graph: ArchitectureGraph) -> bool:
    has_queue = any(c.type == "queue" for c in graph.components)
    has_workers = any(c.type == "worker" for c in graph.components)
    return has_queue and has_workers
```

### **2. Spatial Layer Detection**
Use x-coordinates to infer architecture layers:

```python
def detect_layers(graph: ArchitectureGraph) -> Dict[str, List[str]]:
    layers = {"frontend": [], "backend": [], "data": []}

    for comp in graph.components:
        x = comp.position["x"]
        if x < 200:
            layers["frontend"].append(comp.id)
        elif 200 <= x < 400:
            layers["backend"].append(comp.id)
        else:
            layers["data"].append(comp.id)

    return layers
```

### **3. Anti-Pattern Detection**

```python
class CriticAgent:
    def find_single_point_of_failure(self, graph: ArchitectureGraph) -> List[ArchitectureIssue]:
        """Detect components with no redundancy"""
        issues = []

        for comp in graph.components:
            if comp.type == "database":
                # Check if there's a replica/backup
                has_replica = any(
                    c.type == "database" and c.id != comp.id
                    for c in graph.components
                )
                if not has_replica:
                    issues.append(ArchitectureIssue(
                        issue_type="reliability",
                        severity="critical",
                        description=f"Single database '{comp.name}' with no replica",
                        affected_components=[comp.id],
                        recommendation="Add database replica for high availability"
                    ))

        return issues
```

---

## **VI. FastAPI Integration**

### **1. Endpoint Structure**
```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="HLD Agent API")

@app.post("/analyze", response_model=AgentResponse)
async def analyze_canvas(canvas: ExcalidrawCanvas) -> AgentResponse:
    """Analyze provided Excalidraw canvas"""
    try:
        # Parse → Analyze → Suggest
        graph = parser.parse(canvas.dict())
        analysis = analyzer.analyze(graph)
        suggestions = await agent_orchestrator.run(graph)

        return AgentResponse(
            canvas_hash=hash_canvas(canvas),
            architecture_summary=analysis.summary,
            suggestions=suggestions,
            # ...
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### **2. Background Polling**
```python
from fastapi import BackgroundTasks

@app.on_event("startup")
async def start_canvas_monitor():
    """Start background polling task"""
    monitor = CanvasMonitor(
        file_path="/path/to/temp.excalidraw",
        poll_interval=60  # 1 minute
    )
    asyncio.create_task(monitor.start_polling())

# Canvas monitor detects changes and triggers analysis
class CanvasMonitor:
    async def start_polling(self):
        while True:
            await asyncio.sleep(self.poll_interval)

            content = read_file(self.file_path)
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            if content_hash != self.last_hash:
                logger.info("Canvas changed, triggering analysis")
                await self.trigger_analysis(content)
                self.last_hash = content_hash
```

### **3. Health Check Endpoint**
```python
@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "llm_available": await check_llm_connection(),
        "canvas_monitored": monitor.is_running(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## **VII. Testing Requirements**

### **1. Unit Tests (Mandatory)**
```python
# tests/test_parser.py
def test_parse_simple_canvas():
    """Test parsing basic three-tier architecture"""
    with open("tests/fixtures/simple_three_tier.excalidraw") as f:
        canvas = json.load(f)

    graph = ExcalidrawParser().parse(canvas)

    assert len(graph.components) == 3
    assert graph.components[0].name == "user"
    assert len(graph.connections) == 2
```

### **2. Integration Tests**
```python
# tests/test_agents.py
@pytest.mark.asyncio
async def test_next_component_agent():
    """Test agent suggests relevant components"""
    graph = ArchitectureGraph(
        components=[
            ComponentNode(id="1", name="API Gateway", type="api-gateway", position={"x": 100, "y": 100})
        ],
        connections=[]
    )

    suggestions = await NextComponentAgent().suggest(graph)

    assert len(suggestions) > 0
    assert any(s.component_type in ["database", "cache", "service"] for s in suggestions)
```

### **3. Test Fixtures**
- Keep diverse sample Excalidraw files in `tests/fixtures/sample_canvases/`
- Cover: simple architectures, complex microservices, anti-patterns, incomplete flows

---

## **VIII. Configuration Management**

### **1. Environment Variables**
```python
# .env file
GROQ_API_KEY=your_key_here
LANGSMITH_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here

LOG_LEVEL=INFO
POLL_INTERVAL=60
MAX_SUGGESTIONS=5
```

### **2. YAML Configuration**
```yaml
# config/config.yaml
llm:
  provider: "groq"
  models:
    primary: "llama-3.3-70b-versatile"
    fallback: "gemma2-9b-it"
  temperature: 0.1
  max_tokens: 700
  timeout: 30

agents:
  enabled:
    - next_component
    - pattern_completion
    - critic
  max_parallel: 3

suggestions:
  max_count: 5
  min_confidence: 0.3
  prioritize_incomplete_flows: true
```

---

## **IX. Security & Safety**

### **1. Input Validation**
```python
# ✅ GOOD - Validate all inputs
@app.post("/analyze")
async def analyze_canvas(canvas: ExcalidrawCanvas):  # Pydantic validates
    if len(canvas.elements) > 1000:
        raise HTTPException(400, "Canvas too large (max 1000 elements)")
    # ...

# ❌ BAD - No validation
@app.post("/analyze")
async def analyze_canvas(canvas: dict):  # Unvalidated
    # ...
```

### **2. No Secrets in Logs**
```python
# ✅ GOOD
logger.info(f"Canvas analyzed", extra={"component_count": len(graph.components)})

# ❌ BAD
logger.info(f"Canvas: {canvas.dict()}")  # May contain sensitive user data
```

### **3. Rate Limiting (Future)**
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/analyze")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def analyze_canvas(canvas: ExcalidrawCanvas):
    # ...
```

---

## **X. Performance Optimization**

### **1. Async Everywhere**
```python
# ✅ GOOD
async def run_agents(graph: ArchitectureGraph):
    results = await asyncio.gather(...)

# ❌ BAD
def run_agents(graph):
    r1 = agent1.suggest(graph)  # Blocking
```

### **2. Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def classify_component(name: str) -> str:
    """Cache component type classification"""
    # Expensive LLM call or pattern matching
    return component_type
```

### **3. Timeout All LLM Calls**
```python
async def suggest_with_timeout(graph: ArchitectureGraph, timeout: int = 30):
    try:
        return await asyncio.wait_for(
            llm_client.suggest(graph),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning("LLM timeout, using fallback")
        return default_suggestions(graph)
```

---

## **XI. Monitoring & Observability**

### **1. Structured Logging**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "agent_suggestion_completed",
    agent="next_component",
    canvas_hash=canvas_hash,
    suggestion_count=len(suggestions),
    latency_ms=latency,
    llm_tokens_used=tokens
)
```

### **2. Metrics (Prometheus)**
```python
from prometheus_client import Counter, Histogram

request_count = Counter("api_requests_total", "Total API requests", ["endpoint"])
suggestion_latency = Histogram("suggestion_latency_seconds", "Suggestion generation time")

@app.post("/analyze")
async def analyze_canvas(canvas: ExcalidrawCanvas):
    request_count.labels(endpoint="/analyze").inc()

    with suggestion_latency.time():
        result = await orchestrator.run(graph)

    return result
```

---

## **XII. Summary: Key Rules**

1. ✅ **Always use Pydantic** for data validation
2. ✅ **Structured outputs only** (Instructor + Pydantic)
3. ✅ **Fail-safe defaults** (never crash, return safe fallbacks)
4. ✅ **Async by default** (parallel agent execution)
5. ✅ **Type hints everywhere** (mypy-compliant)
6. ✅ **Structured JSON logging** (queryable, trackable)
7. ✅ **Comprehensive testing** (unit + integration)
8. ✅ **Defensive parsing** (handle malformed Excalidraw gracefully)
9. ✅ **Token-efficient prompts** (truncate context, use smaller models)
10. ✅ **Security first** (validate inputs, no secrets in logs)

---

**This document overrides generic Python guidelines when conflicts arise. When in doubt, favor safety, structure, and testability.**

🚀 **Ready to build production-grade HLD Agent backend!**
