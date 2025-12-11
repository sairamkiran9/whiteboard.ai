# **claude.md — LLM Ruleset for Reliable System Design Copilot (Python)**

This document defines strict guidelines for integrating Claude (or similar LLMs) into a **Python-based system design copilot**.
It ensures **predictable, safe, and context-aware outputs** while preventing hallucinations, insecure suggestions, or architectural errors.

> **📁 Module-Specific Documentation:**
> - **Backend:** See [`backend/CLAUDE.md`](backend/CLAUDE.md) for backend-specific rules (Excalidraw parsing, multi-agent system, FastAPI)
> - **Backend Plan:** See [`backend/PLAN.md`](backend/PLAN.md) for implementation roadmap and architecture

---

## **I. General Principles**

1. **Use Only Production-Ready Frameworks/APIs**

   * Leverage **LangChain**, **MCP**, and Python standard libraries.
   * Never reimplement memory, retrieval, or tokenization logic.

2. **Structured Output Only**

   * LLM must **always return valid JSON objects** following predefined schemas.
   * If output fails validation:

     * Return a **no-op**, **error state**, or **safe default**.
     * Never continue with partially valid data.

3. **Explicit, Unambiguous Prompts**

   * Define exact output formats with clear examples.
   * Avoid vague or open-ended instructions.

4. **Strict Ontology Enforcement**

   * Only allow predefined **node types** and **edge types**.
   * No custom or “magic” services, components, or relationships.

5. **Refuse Unsupported Requests**

   * For out-of-scope requests, LLM must return:

     ```json
     {"suggestion": null, "reasoning": "Request not supported", "reference": null}
     ```

---

## **II. Environment & Python Project Setup**

1. **Use `uv` for Dependency and Virtual Environment Management**

   * Create and activate a virtual environment with:

     ```bash
     uv venv
     source .venv/bin/activate
     ```
   * Install dependencies:

     ```bash
     uv pip install -r requirements.txt
     ```
   * Update and freeze dependencies regularly:

     ```bash
     uv pip freeze > requirements.txt
     ```

2. **Python Code Style and Quality**

   * Follow **PEP 8** for code style.
   * Enforce linting and formatting using:

     ```bash
     uv pip install black flake8 isort
     black .
     flake8 .
     isort .
     ```

3. **Testing Strategy**

   * Implement **unit tests** for:

     * Prompt templates
     * Validation logic
     * LangChain pipeline behavior
   * Implement **integration tests** for:

     * LLM API responses
     * MCP context handling
     * End-to-end diagram suggestion flow
   * Run tests with `pytest`:

     ```bash
     uv pip install pytest
     pytest tests/
     ```

4. **Environment Variables and Secrets**

   * Store API keys and secrets in `.env` files.
   * Load using `python-dotenv`.
   * **Never hardcode secrets** in code or prompts.

---

## **III. Context & State Management**

1. **Use Built-in LangChain Tools**

   * For prompt history and scene state:

     * `langchain.memory`
     * `PromptTemplate`
     * `ConversationBufferMemory`
   * Use MCP context objects for editor ↔ backend messaging.

2. **Never Manually Concatenate Prompt Strings**

   * Always rely on LangChain constructs for safe prompt composition.

3. **Incremental, Context-Aware Suggestions**

   * Suggestions must:

     * Consider the **current scene**.
     * Avoid duplication of existing nodes or edges.

4. **Payload Limits**

   * Hard-cap the size of scene/context payloads before sending to LLM.
   * Truncate or summarize older history to stay within token limits.

---

## **IV. Output Requirements**

* **Valid JSON only**, no Markdown or free text.

* Required response schema:

  ```json
  {
    "suggestion": {
      "nodes": [
        {"type": "cache", "label": "Redis Cache"}
      ],
      "edges": [
        {"from": "api-gateway", "to": "cache", "type": "reads-from"}
      ]
    },
    "reasoning": "Added a cache due to frequent DB reads.",
    "reference": "https://aws.amazon.com/caching/"
  }
  ```

* Allowed **Node Types**:

  ```
  client, webserver, api-gateway, cache, database, worker, queue, storage
  ```

* Allowed **Edge Types**:

  ```
  requests, reads-from, writes-to, sends-message, connects-to, depends-on
  ```

* If no suggestion is appropriate:

  ```json
  {"suggestion": null, "reasoning": "No further suggestions", "reference": null}
  ```

---

## **V. Security & Safety Rules**

1. **No PII or secrets** in any prompts, responses, or logs.
2. **No insecure designs**, including:

   * Direct DB access from client applications.
   * Plaintext or unencrypted communication channels.
3. **Audit and Log**:

   * Log every LLM request and response for debugging and auditing.
   * Use Python logging with structured JSON output.
4. **Debounce/Throttle LLM Calls**:

   * Implement rate limiting to avoid flooding the LLM API.

---

## **VI. Python Integration Guidelines**

1. **LangChain Usage**

   * Use only LangChain-native components:

     * `PromptTemplate`
     * `LLMChain`
     * `RunnableSequence`
     * `Memory`
   * Avoid writing custom chain orchestration unless necessary.

2. **Validation First**

   * Validate LLM outputs against a JSON Schema using `pydantic` or `jsonschema`.
   * Example validation:

     ```python
     from pydantic import BaseModel, ValidationError

     class Node(BaseModel):
         type: str
         label: str

     class Edge(BaseModel):
         from_: str
         to: str
         type: str

     class Suggestion(BaseModel):
         nodes: list[Node]
         edges: list[Edge]
     ```

3. **Error Handling**

   * If validation fails or model refuses, return a safe default or display an error state.

4. **Logging**

   * Save all LLM requests and responses to `logs/llm/` with timestamps.
   * Example:

     ```bash
     logs/llm/2025-09-04-15-30.json
     ```

5. **No Direct File Operations by LLM**

   * LLM can never read or write files.
   * Only backend Python code can handle file access.

---

## **VII. Example Prompt**

```plaintext
You are a Python-based architectural copilot for system design diagrams.

- Respond ONLY with valid JSON.
- You may ONLY use these node types: ["client", "webserver", "api-gateway", "cache", "database", "worker", "queue", "storage"]
- You may ONLY use these edge types: ["requests", "reads-from", "writes-to", "connects-to", "sends-message", "depends-on"]

Given this current scene state:
{ ...scene JSON... }

Suggest up to 2 new nodes or edges, include 'reasoning' and 'reference'.
If nothing is appropriate, return:
{"suggestion": null, "reasoning": "No further suggestions", "reference": null}
```

---

## **VIII. Deployment Best Practices**

1. Deploy using **FastAPI** or **Flask** for LLM service endpoints.
2. Use **MCP** or WebSockets for editor ↔ backend messaging.
3. Scale using **Docker** and **Kubernetes**.
4. Monitor LLM performance and errors with **Prometheus** + **Grafana**.

---

## **IX. HLD Agent Integration**

The project includes a **production-ready, modular HLD Agent** located at `backend/hld_agent/`:

### **Usage in FastAPI**

```python
from hld_agent import HLDAgent
from hld_agent.core.exceptions import HLDAgentError

# Initialize agent (uses config/config.yaml)
hld_agent = HLDAgent()

# Generate architecture suggestions
try:
    result = hld_agent.generate_architecture_suggestion(
        current_sequence="user req -> load balancer",
        context="distributed job scheduler"
    )
    
    if result["success"]:
        # Convert to frontend format
        return convert_agent_result_to_response(result)
    else:
        # Handle failure case
        return safe_fallback_response()
        
except HLDAgentError as e:
    logger.error(f"HLD Agent error: {e}")
    return error_response(str(e))
```

### **Key Features**

* **Exact Logic Preservation**: Maintains all original prompts and behavior
* **Configuration Management**: YAML config with environment variables  
* **Structured Logging**: JSON logs with correlation IDs
* **Comprehensive Testing**: Unit and integration test coverage
* **Error Handling**: Graceful degradation and recovery
* **Health Monitoring**: Built-in status checks

### **Configuration**

```yaml
# backend/hld_agent/config/config.yaml
llm:
  provider: "groq"
  models:
    primary: "gemma2-9b-it"
    fallback: "deepseek-r1-distill-llama-70b"
  max_iterations: 6

api_keys:
  groq_api_key: "${GROQ_API_KEY}"

logging:
  level: "INFO"
  format: "json"
```

See `backend/hld_agent/README.md` for complete documentation.

---

## **X. Summary**

By following this ruleset:

* Outputs are **safe**, **validated**, and **context-aware**.
* LLM integration remains **clean, modular, and testable**.
* Bugs, hallucinations, and insecure suggestions are **minimized**.
* **Production-ready HLD Agent** provides reliable architecture suggestions.

> **Store this file** as `/docs/claude.md` and **version-control it** to enforce team-wide consistency.

- use langgraph and langchain inbuilt or library methods, dont' implement from scratch